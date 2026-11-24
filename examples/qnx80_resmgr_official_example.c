/*
 * Copyright (c) 2026 QX-PROBE contributors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*
 * qnx80_resmgr_official_example.c
 *
 * The OFFICIAL EXAMPLE of the QNX SDP 8.0 documentation, made to compile.
 *
 * Source: iofunc_func_init() — "Fill a connect and I/O function table with the
 * POSIX-layer defaults".  The page overrides the read handler with:
 *
 *     my_io_functions.io_read = my_io_read;
 *
 * The real qcc of the SDP 8.0 (gcc_ntox86_64, 24 November 2026) REJECTS that
 * line: "'resmgr_io_funcs_t' {aka 'struct _resmgr_io_funcs'} has no member
 * named 'io_read'; did you mean 'read'?".  <sys/resmgr.h> of the SDP 8.0
 * declares the member "read".  This file therefore writes ".read": it is
 * the documentation's example, with the one change the compiler requires.
 *
 * This file exercises one thing the checker ignored before cycle 156:
 *   the table name: here "my_io_functions", not "io_funcs".
 *
 * What the checker reports on this file: NOTHING.  No actionable finding
 * (0 ERROR, 0 WARN), and qcc -Vgcc_ntox86_64 -Werror builds it.
 *
 * Official QNX SDP 8.0 sources:
 *   iofunc_func_init()   https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html
 *   resmgr_io_funcs_t()  https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html
 *   iofunc_read_verify() https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_verify.html
 *   <sys/resmgr.h>       the header of the SDP 8.0 (target/qnx/usr/include)
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/iofunc.h>
#include <sys/dispatch.h>
#include <sys/resmgr.h>

static resmgr_connect_funcs_t my_connect_functions;
static resmgr_io_funcs_t my_io_functions;
static iofunc_attr_t attr;

static int my_io_read(resmgr_context_t *ctp, io_read_t *msg, RESMGR_OCB_T *ocb)
{
    int status;
    char value = 'x';

    /* The access gate: mandatory for every read handler. */
    if ((status = iofunc_read_verify(ctp, msg, ocb, NULL)) != EOK)
        return status;

    _IO_SET_READ_NBYTES(ctp, 1);
    SETIOV(ctp->iov, &value, 1);
    return _RESMGR_NPARTS(1);
}

int main(void)
{
    dispatch_t         *dpp;
    dispatch_context_t *ctp;
    resmgr_attr_t       resmgr_attr;
    int                 id;

    dpp = dispatch_create();
    if (dpp == NULL) {
        fprintf(stderr, "qx-probe-official: unable to create dispatch handle\n");
        return EXIT_FAILURE;
    }

    memset(&resmgr_attr, 0, sizeof resmgr_attr);
    resmgr_attr.nparts_max  = 1;

    /* The POSIX defaults ... */
    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &my_connect_functions,
                     _RESMGR_IO_NFUNCS, &my_io_functions);

    /* ... then the override (".read": the member declared by QNX 8.0). */
    my_io_functions.read = my_io_read;

    iofunc_attr_init(&attr, S_IFNAM | 0666, 0, 0);

    id = resmgr_attach(dpp, &resmgr_attr, "/dev/qxprobe-official",
                       _FTYPE_ANY, 0, &my_connect_functions, &my_io_functions, &attr);
    if (id == -1) {
        fprintf(stderr, "qx-probe-official: unable to attach name\n");
        return EXIT_FAILURE;
    }

    ctp = dispatch_context_alloc(dpp);
    while (1) {
        if ((ctp = dispatch_block(ctp)) == NULL) {
            fprintf(stderr, "qx-probe-official: block error\n");
            return EXIT_FAILURE;
        }
        dispatch_handler(ctp);
    }
    return EXIT_SUCCESS;
}

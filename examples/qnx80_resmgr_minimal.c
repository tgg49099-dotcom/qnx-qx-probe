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
 * qnx80_resmgr_minimal.c
 *
 * MINIMAL and CANONICAL example of a QNX 8.0 resource manager, written for
 * QX-PROBE.  It is deliberately complete and readable: it is the reference
 * the checker is tested against.
 *
 * What the checker reports on this file: NOTHING.  No actionable finding
 * (0 ERROR, 0 WARN) — this is valid QNX 8.0 code.
 *
 * APIs used (official QNX SDP 8.0 documentation):
 *   resmgr_attach()      https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html
 *   iofunc_func_init()   https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_func_init.html
 *   iofunc_read_verify() https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_read_verify.html
 *   iofunc_write_verify()https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/i/iofunc_write_verify.html
 *   _RESMGR_NPARTS()     https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/_resmgr_nparts.html
 *   dispatch_block()     https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_block.html
 *   dispatch_handler()   https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/d/dispatch_handler.html
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/iofunc.h>
#include <sys/dispatch.h>
#include <sys/resmgr.h>

static resmgr_connect_funcs_t connect_funcs;
static resmgr_io_funcs_t io_funcs;
static iofunc_attr_t attr;

static int qx_read(resmgr_context_t *ctp, io_read_t *msg, iofunc_ocb_t *ocb)
{
    int status;
    char value = 'x';

    /* The access gate: mandatory for every read handler. */
    if ((status = iofunc_read_verify(ctp, msg, ocb, NULL)) != EOK)
        return status;

    _IO_SET_READ_NBYTES(ctp, 1);
    SETIOV(ctp->iov, &value, 1);

    /* The number of parts returned to the client (1 component in the IOV). */
    return _RESMGR_NPARTS(1);
}

static int qx_write(resmgr_context_t *ctp, io_write_t *msg, iofunc_ocb_t *ocb)
{
    int status;

    if ((status = iofunc_write_verify(ctp, msg, ocb, NULL)) != EOK)
        return status;

    _IO_SET_WRITE_NBYTES(ctp, 0);
    return _RESMGR_NPARTS(0);
}

int main(void)
{
    dispatch_t         *dpp;
    dispatch_context_t *ctp;
    resmgr_attr_t       resmgr_attr;
    int                 id;

    dpp = dispatch_create();
    if (dpp == NULL) {
        fprintf(stderr, "qx-probe-demo: unable to create dispatch handle\n");
        return EXIT_FAILURE;
    }

    memset(&resmgr_attr, 0, sizeof resmgr_attr);
    resmgr_attr.nparts_max  = 1;      /* one component in ctp->iov */
    resmgr_attr.msg_max_size = 2048;

    /* The POSIX defaults first, then our own overrides. */
    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,
                     _RESMGR_IO_NFUNCS, &io_funcs);
    io_funcs.read  = qx_read;
    io_funcs.write = qx_write;

    iofunc_attr_init(&attr, S_IFNAM | 0666, 0, 0);

    id = resmgr_attach(dpp, &resmgr_attr, "/dev/qxprobe-demo",
                       _FTYPE_ANY, 0, &connect_funcs, &io_funcs, &attr);
    if (id == -1) {
        fprintf(stderr, "qx-probe-demo: unable to attach name\n");
        return EXIT_FAILURE;
    }

    ctp = dispatch_context_alloc(dpp);
    while (1) {
        if ((ctp = dispatch_block(ctp)) == NULL) {
            fprintf(stderr, "qx-probe-demo: block error\n");
            return EXIT_FAILURE;
        }
        dispatch_handler(ctp);
    }
    return EXIT_SUCCESS;
}

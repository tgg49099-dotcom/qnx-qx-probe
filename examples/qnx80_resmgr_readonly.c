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
 * qnx80_resmgr_readonly.c
 *
 * READ-ONLY QNX 8.0 resource manager, attached OUTSIDE /dev/.
 *
 * The two historical QX-PROBE false positives lived exactly here:
 *   1. the mount point is "/var/run/qxprobe-status" and not "/dev/...";
 *   2. io_funcs.write is not wired: the manager is read-only.
 *
 * Both are VALID in QNX 8.0:
 *   - resmgr_attach() "puts the path into the general pathname space";
 *   - resmgr_io_funcs_t provides a POSIX default for every slot
 *     (iofunc_write_default()), and a manager may expose reads only.
 *
 * What the checker reports on this file: NOTHING.  No actionable finding
 * (0 ERROR, 0 WARN).
 *
 * Official QNX SDP 8.0 sources:
 *   resmgr_attach()     https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_attach.html
 *   resmgr_io_funcs_t   https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.lib_ref/topic/r/resmgr_io_funcs_t.html
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

static int qx_status_read(resmgr_context_t *ctp, io_read_t *msg, iofunc_ocb_t *ocb)
{
    int  status;
    char value = 's';

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
        fprintf(stderr, "qx-probe-status: unable to create dispatch handle\n");
        return EXIT_FAILURE;
    }

    memset(&resmgr_attr, 0, sizeof resmgr_attr);
    resmgr_attr.nparts_max  = 1;
    resmgr_attr.msg_max_size = 2048;

    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,
                     _RESMGR_IO_NFUNCS, &io_funcs);

    /* Read-only: io_funcs.write is deliberately not wired. */
    io_funcs.read = qx_status_read;

    iofunc_attr_init(&attr, S_IFNAM | 0444, 0, 0);

    /* Mount point outside /dev/: valid in the general pathname space. */
    id = resmgr_attach(dpp, &resmgr_attr, "/var/run/qxprobe-status",
                       _FTYPE_ANY, 0, &connect_funcs, &io_funcs, &attr);
    if (id == -1) {
        fprintf(stderr, "qx-probe-status: unable to attach name\n");
        return EXIT_FAILURE;
    }

    ctp = dispatch_context_alloc(dpp);
    while (1) {
        if ((ctp = dispatch_block(ctp)) == NULL) {
            fprintf(stderr, "qx-probe-status: block error\n");
            return EXIT_FAILURE;
        }
        dispatch_handler(ctp);
    }
    return EXIT_SUCCESS;
}

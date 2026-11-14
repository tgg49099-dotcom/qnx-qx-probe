/* The read handler of the split resource manager: no table, no attach. */
#include <errno.h>
#include <sys/iofunc.h>
#include <sys/dispatch.h>

int split_read(resmgr_context_t *ctp, io_read_t *msg, RESMGR_OCB_T *ocb)
{
    int status;
    if ((status = iofunc_read_verify(ctp, msg, ocb, NULL)) != EOK) {
        return status;
    }
    _IO_SET_READ_NBYTES(ctp, 0);
    return _RESMGR_NPARTS(0);
}

/* Resource manager split over three files, as larger QNX services are:
 * split_main.c wires the tables and attaches the path, split_io_read.c holds
 * the read handler, split_loop.c holds the message loop.  Correct code. */
#include <sys/iofunc.h>
#include <sys/dispatch.h>

extern int split_read(resmgr_context_t *ctp, io_read_t *msg, RESMGR_OCB_T *ocb);
extern int split_run(dispatch_t *dpp);

static resmgr_connect_funcs_t connect_funcs;
static resmgr_io_funcs_t      io_funcs;
static iofunc_attr_t          attr;

int main(void)
{
    dispatch_t *dpp = dispatch_create();
    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,
                     _RESMGR_IO_NFUNCS, &io_funcs);
    io_funcs.read = split_read;
    iofunc_attr_init(&attr, S_IFCHR | 0444, NULL, NULL);
    if (resmgr_attach(dpp, NULL, "/dev/split", _FTYPE_ANY, 0,
                      &connect_funcs, &io_funcs, &attr) == -1) {
        return 1;
    }
    return split_run(dpp);
}

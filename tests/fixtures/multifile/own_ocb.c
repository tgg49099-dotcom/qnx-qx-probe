/* A resource manager that binds its OWN OCB with resmgr_open_bind() and never
 * uses the iofunc OCB layer: iofunc_read_verify() takes an iofunc_ocb_t and
 * cannot be called here.  The missing gate is reported as INFO only. */
#include <errno.h>
#include <stdlib.h>
#include <sys/iofunc.h>
#include <sys/dispatch.h>

struct my_ocb { int pos; };

static resmgr_connect_funcs_t connect_funcs;
static resmgr_io_funcs_t      io_funcs;
static iofunc_attr_t          attr;

static int my_open(resmgr_context_t *ctp, io_open_t *msg, void *extra)
{
    struct my_ocb *o = calloc(1, sizeof *o);
    if (o == NULL || resmgr_open_bind(ctp, o, &io_funcs) == -1) {
        free(o);
        return ENOMEM;
    }
    return EOK;
}

static int my_read(resmgr_context_t *ctp, io_read_t *msg, void *ocb)
{
    struct my_ocb *o = ocb;
    o->pos++;
    _IO_SET_READ_NBYTES(ctp, 0);
    return _RESMGR_NPARTS(0);
}

int main(void)
{
    dispatch_t *dpp = dispatch_create();
    dispatch_context_t *ctp;
    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,
                     _RESMGR_IO_NFUNCS, &io_funcs);
    connect_funcs.open = my_open;
    io_funcs.read = my_read;
    iofunc_attr_init(&attr, S_IFCHR | 0444, NULL, NULL);
    if (resmgr_attach(dpp, NULL, "/dev/myocb", _FTYPE_ANY, 0,
                      &connect_funcs, &io_funcs, &attr) == -1) {
        return 1;
    }
    ctp = dispatch_context_alloc(dpp);
    for (;;) {
        if ((ctp = dispatch_block(ctp)) == NULL) {
            return 1;
        }
        dispatch_handler(ctp);
    }
}

/* Attaches at the root of the path space with an empty path, as a
 * path manager does.  An empty path is not a relative path. */
#include <sys/iofunc.h>
#include <sys/dispatch.h>

static resmgr_connect_funcs_t connect_funcs;
static resmgr_io_funcs_t      io_funcs;
static iofunc_attr_t          attr;

int main(void)
{
    dispatch_t *dpp = dispatch_create();
    dispatch_context_t *ctp;
    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs,
                     _RESMGR_IO_NFUNCS, &io_funcs);
    iofunc_attr_init(&attr, S_IFDIR | 0555, NULL, NULL);
    if (resmgr_attach(dpp, NULL, "", _FTYPE_ANY, _RESMGR_FLAG_DIR,
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

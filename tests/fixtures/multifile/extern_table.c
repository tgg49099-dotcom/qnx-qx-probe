/* A handler that names, inside a function, a table defined in another file.
 * "extern" in block scope declares the table: it is not an automatic,
 * uninitialised table. */
#include <sys/iofunc.h>
#include <sys/dispatch.h>

int ext_open(resmgr_context_t *ctp, io_open_t *msg, void *extra)
{
    extern resmgr_io_funcs_t ext_io_funcs;
    static int ocb;
    return resmgr_open_bind(ctp, &ocb, &ext_io_funcs) == -1 ? -1 : 0;
}

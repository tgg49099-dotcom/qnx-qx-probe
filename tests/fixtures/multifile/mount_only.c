/* A mount helper: it registers for mount requests only, as the QNX 8.0
 * guide "Writing a Resource Manager" describes ("register a NULL path with
 * an FTYPE of _FTYPE_MOUNT and with the flag _RESMGR_FLAG_FTYPEONLY"), with
 * the mount callout in the connect table and no I/O table at all. */
#include <sys/iofunc.h>
#include <sys/dispatch.h>
#include <sys/mount.h>

static resmgr_connect_funcs_t mount_connect;
static iofunc_attr_t          handle;

static int my_mount(resmgr_context_t *ctp, io_mount_t *msg,
                    RESMGR_HANDLE_T *h, io_mount_extra_t *extra)
{
    (void)ctp; (void)msg; (void)h; (void)extra;
    return ENOENT;
}

int main(void)
{
    dispatch_t *dpp = dispatch_create();
    dispatch_context_t *ctp;
    resmgr_attr_t rattr = { 0 };
    mount_connect.mount = my_mount;
    if (resmgr_attach(dpp, &rattr, NULL, _FTYPE_MOUNT,
                      _RESMGR_FLAG_DIR | _RESMGR_FLAG_FTYPEONLY,
                      &mount_connect, NULL, &handle) == -1) {
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

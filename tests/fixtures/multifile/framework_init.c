/* A server that receives private messages only: resmgr_attach() is called
 * with a NULL path just to set up the resource-manager layer of the dispatch
 * framework, then message_attach() binds its own message range.  The QNX
 * documentation of resmgr_attach(): "If path is NULL, only the first step
 * will be done" (the framework set-up), so the two tables are not used and
 * NULL is correct there. */
#include <sys/iofunc.h>
#include <sys/dispatch.h>

#define MY_MSG_FIRST (_IO_MAX + 1)
#define MY_MSG_LAST  (_IO_MAX + 16)

static int my_msg(message_context_t *ctp, int code, unsigned flags, void *handle)
{
    (void)code; (void)flags; (void)handle;
    return MsgReply(ctp->rcvid, EOK, NULL, 0);
}

int main(void)
{
    dispatch_t *dpp = dispatch_create();
    dispatch_context_t *ctp;
    resmgr_attr_t rattr = { 0 };
    rattr.nparts_max = 1;
    if (resmgr_attach(dpp, &rattr, NULL, 0, 0, NULL, NULL, NULL) == -1) {
        return 1;
    }
    if (message_attach(dpp, NULL, MY_MSG_FIRST, MY_MSG_LAST, my_msg, NULL) == -1) {
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

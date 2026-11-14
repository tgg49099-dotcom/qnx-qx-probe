/* Same server, but with _RESMGR_FLAG_FTYPEONLY: the documentation says the
 * path "must be NULL but the resulting registration is at \"/\"", so the
 * call does bind the tables and NULL tables are a real bug (ERROR QX001). */
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
    if (resmgr_attach(dpp, &rattr, NULL, _FTYPE_ANY, _RESMGR_FLAG_FTYPEONLY, NULL, NULL, NULL) == -1) {
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

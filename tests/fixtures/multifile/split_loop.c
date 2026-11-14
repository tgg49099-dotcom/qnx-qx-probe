/* The message loop of the split resource manager. */
#include <sys/iofunc.h>
#include <sys/dispatch.h>

int split_run(dispatch_t *dpp)
{
    dispatch_context_t *ctp = dispatch_context_alloc(dpp);
    for (;;) {
        if ((ctp = dispatch_block(ctp)) == NULL) {
            return 1;
        }
        dispatch_handler(ctp);
    }
}

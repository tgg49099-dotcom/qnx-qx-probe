/*
 * Copyright (c) 2025, BlackBerry Limited. All rights reserved.
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


#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <errno.h>
#include <string.h>
#include <sys/iofunc.h>
#include <sys/dispatch.h>
#include <sys/resmgr.h>
#include "sys/eventfd.h"

typedef struct {
    iofunc_attr_t attr;     // Inherit standard attributes
    uint64_t counter;       // Counter value
} eventfd_attr_t;

static resmgr_connect_funcs_t connect_funcs;
static resmgr_io_funcs_t io_funcs;

int io_read(resmgr_context_t *ctp, io_read_t *msg, RESMGR_OCB_T *ocb) {
    int status, nparts;
    size_t nbytes;
    eventfd_attr_t *eventfd_attr = (eventfd_attr_t *)ocb->attr;
    uint64_t value = eventfd_attr->counter;

    /* check to see if the read operation is allowed */
    if ((status = iofunc_read_verify(ctp, msg, ocb, NULL)) != EOK)
        return status;
    /*
        Check if type is _IO_XTYPE_NONE. otherwise return ENOSYS
        Meaning it doesnt handle other read functions like pread
    */
    if ((msg->i.xtype & _IO_XTYPE_MASK) != _IO_XTYPE_NONE)
        return ENOSYS;

    /* eventfd flag handling */    
    if(ocb->ioflag & O_NONBLOCK && value == 0)
        return EAGAIN;

    nbytes = _IO_READ_GET_NBYTES(msg);
    
    /* 
        set up the return data IOV 
        alywats read 8 bytes (uint64_t)
    */
    SETIOV(ctp->iov, &value, nbytes);

    /* set up the number of bytes (returned by client's read()) */
    _IO_SET_READ_NBYTES(ctp, nbytes);
    nparts = 1;

    /* reset counter to 0 after read operation*/
    eventfd_attr->counter = 0;

    /* mark the access time as invalid (we just accessed it) */
    if (msg->i.nbytes > 0)
        ocb->attr->flags |= IOFUNC_ATTR_ATIME;

    /* return the number of bytes that were read*/
    return _RESMGR_NPARTS(nparts);
}


int io_write(resmgr_context_t *ctp, io_write_t *msg, RESMGR_OCB_T *ocb) {
    int status, nparts;
    size_t nbytes;
    eventfd_attr_t *eventfd_attr = (eventfd_attr_t *)ocb->attr;
    uint64_t value;

    /* check to see if the write operation is allowed */
    if ((status = iofunc_write_verify(ctp, msg, ocb, NULL)) != EOK)
        return status;

    /*
        Check if type is _IO_XTYPE_NONE. otherwise return ENOSYS
        Meaning it doesnt handle other write functions like pwrite
    */
    if ((msg->i.xtype & _IO_XTYPE_MASK) != _IO_XTYPE_NONE)
        return ENOSYS;

    /* Extract the length of the client's message */
    nbytes = _IO_WRITE_GET_NBYTES(msg);

    /* Ensure we're receiving exactly a uint64_t */
    if (nbytes != sizeof(uint64_t)) {
        printf("Invalid write size: %zu bytes (expected %zu)\n", nbytes, sizeof(uint64_t));
        return EINVAL;
    }

    /* Read the data from the sender's message */
    resmgr_msgread(ctp, &value, sizeof(value), sizeof(io_write_t));

    eventfd_attr->counter = value;
    nparts = 0;

    /* set up the number of bytes (returned by client's write()) */
    _IO_SET_WRITE_NBYTES(ctp, nbytes);

    /* mark the access time as invalid (we just accessed it) */
    if (nbytes > 0)
        ocb->attr->flags |= IOFUNC_ATTR_MTIME | IOFUNC_ATTR_CTIME;

    return _RESMGR_NPARTS(nparts);
}


int main(int argc, char **argv)
{
    /* declare variables we'll be using */
    resmgr_attr_t        resmgr_attr;
    dispatch_t           *dpp;
    dispatch_context_t   *ctp;
    int                  id;
    eventfd_attr_t eattr;

    /* initialize dispatch interface */
    dpp = dispatch_create_channel(-1, DISPATCH_FLAG_NOLOCK );
    if (dpp == NULL) {
        fprintf(stderr, "%s: Unable to allocate dispatch handle.\n", argv[0]);
        return EXIT_FAILURE;
    }

    /* initialize resource manager attributes */
    memset(&resmgr_attr, 0, sizeof resmgr_attr);
    resmgr_attr.nparts_max = 1;
    resmgr_attr.msg_max_size = 2048;

    /* initialize functions for handling messages */
    iofunc_func_init(_RESMGR_CONNECT_NFUNCS, &connect_funcs, 
                     _RESMGR_IO_NFUNCS, &io_funcs);

    io_funcs.read = io_read;
    io_funcs.write = io_write;

    /* initialize attribute structure used by the device */
    iofunc_attr_init(&eattr.attr, S_IFNAM | 0666, 0, 0);
    eattr.attr.nbytes = sizeof(uint64_t); // eventfd counter size
    eattr.counter = 0;  // Default value

    /* attach our device name */
    id = resmgr_attach(
            dpp,            /* dispatch handle        */
            &resmgr_attr,   /* resource manager attrs */
            "/dev/eventfd", /* device name            */
            _FTYPE_ANY,     /* open type              */
            0,              /* flags                  */
            &connect_funcs, /* connect routines       */
            &io_funcs,      /* I/O routines           */
            &eattr.attr);   /* handle                 */

    if(id == -1) {
        fprintf(stderr, "%s: Unable to attach name.\n", argv[0]);
        return EXIT_FAILURE;
    }

    /* allocate a context structure */
    ctp = dispatch_context_alloc(dpp);

    /* start the resource manager message loop */
    while(1) {
        if((ctp = dispatch_block(ctp)) == NULL) {
            fprintf(stderr, "block error\n");
            return EXIT_FAILURE;
        }
        dispatch_handler(ctp);
    }
    return EXIT_SUCCESS;
}
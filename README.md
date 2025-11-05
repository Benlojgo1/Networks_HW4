# Networks_HW4
## Goal
This repository contains the code solution to the Homework 4: Concurrent Connection HTTP Server. The code will be an extension of the Homework 3: HTTP Server which will update the code to accept concurrent connections. 

## How to run
```
./http_server_conc -p <port> -maxclient <numconn> -maxtotal <numconn>
```
Where `<port>` is the server and the `<numconn>` are the maximum conccurent connections per client and the maximum connections per server

## Questions
1. What is your strategy for identifying unique clients?
2. How do you prevent the clients from opening more connections once they have opened the maximum number of connections?
3. Report the times and speedup for concurrent fetch of the URLs in testcase 1 and 2 wiht the stock http server.
4. Report the times and speedup for the concurrent fetch of the URLs in testcase 1 and 2 with your http_server_conc. Are these the same numbers as above? Why or why not?

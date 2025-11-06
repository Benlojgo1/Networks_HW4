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
   - By combining both the IP address and the user agent header for a unique ID.
2. How do you prevent the clients from opening more connections once they have opened the maximum number of connections?
   - By creating a try_reserve_slot() function that checks if total connections have exceeded max number (via global variables), if so, it sends the error message    "Too Many Requests" and closes the connection.
3. Report the times and speedup for concurrent fetch of the URLs in testcase 1 and 2 wiht the stock http server.
   - python client_conc.py testcase1.txt 1 = 1 connections finished in 0.18 seconds
   - python client_conc.py testcase1.txt 10 = 10 connections finished in 0.09 seconds
   - python client_conc.py testcase2.txt 1 = 1 connections finished in 0.03 seconds
   - python client_conc.py testcase2.txt 10 = 10 connections finished in 0.09 seconds
4. Report the times and speedup for the concurrent fetch of the URLs in testcase 1 and 2 with your http_server_conc. Are these the same numbers as above? Why or why not?
     python client_conc.py testcase1.txt 1 = 1 connections finished in 10.25 seconds
     python client_conc.py testcase1.txt 10 = 10 connections finished in 2.11 seconds
     python client_conc.py testcase2.txt 1 = 1 connections finished in 10.27 seconds
     python client_conc.py testcase2.txt 10 = 10 connections finished in 2.12 seconds
   No, the numbers above are much smaller and it's much faster than our server because it has less concurrency overhead and no connection-limiting logic. Our server adds thread and lock management for enforcing limits, which increases    processing time per request.


Project Team Members and Contributions:
Remy Olivacce (UID: 6105014) - Contributed to the development of the server and client code, handled debugging, and wrote the README file.
High Level Design:
Server:
The server application listens for incoming connections from clients on a specified port. Upon receiving a connection request, it initiates a 3-way handshake with the client to establish a TCP-like connection. Once the connection is established, the server waits to receive data packets from the client. It acknowledges received packets and stores the data in a file. After receiving all data packets, the server terminates the connection.

Client:
The client application connects to the server using the server's IP address and port number. It initiates a 3-way handshake with the server to establish a connection. Once the connection is established, the client reads data from a specified file and sends it to the server in packets. After sending all data packets, the client initiates connection termination by sending a FIN packet to the server. It waits for an acknowledgment from the server and then closes the connection.

Problems Encountered and Solutions:
Execution Errors: There were issues with executing the code, possibly due to incorrect configurations or dependencies. This was resolved by carefully reviewing the code and ensuring all dependencies were installed correctly. Additionally, debugging techniques such as print statements were used to identify and fix errors.
Networking Issues: Troubleshooting network connectivity issues between the server and client virtual machines. This was resolved by ensuring that the virtual machines were configured correctly, and network emulation settings were applied as needed.
Packet Loss and Delay: Dealing with packet loss and delay in the simulated network environment. This was addressed by configuring network emulation settings using the provided script and adjusting parameters as necessary to mimic real-world conditions.
Additional Libraries Used:
No additional libraries were used in this project.

Acknowledgements:
The provided project skeleton and materials were referenced for guidance.
Online tutorials and documentation related to Python socket programming and network emulation were consulted for understanding and troubleshooting.

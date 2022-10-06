# NuttyNios-Client

This repository continuously reads the stream of accelerometer data sent by the FPGA to `nios2-terminal`. It then computes the tilt direction of the board and publishes to NuttyNios-Server.

## Overview
- Thresholding was first perfomed to determine the direction the board was moved in each sample. These were then added to a circular buffer. The board was deemed to be moved in a particular direction if all directions in the buffer were same. 
    - Thresholding and buferring reduced noise. Furthermore, processing at this stage was done to reduce the load on the board and server.
- Direction information is published to the server. Alternatively, the client listens to game difficulty and score information which are then passed to the FPGA for display.
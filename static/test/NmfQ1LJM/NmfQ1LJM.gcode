(Scribbled version of E:/drawbo/static/test/NmfQ1LJM/NmfQ1LJM.svg @ 3500.00)
( E:\drawbo\manage.py run )
G21 (metric ftw)
G90 (absolute mode)
G92 X0.00 Y0.00 Z0.00 (you are here)

M300 S30 (pen down)
G4 P150 (wait 150ms)
M300 S50 (pen up)
G4 P150 (wait 150ms)
M18 (disengage drives)
M01 (Was registration test successful?)
M17 (engage drives if YES, and continue)

Layer 0
(Polyline consisting of 1 segments.)
G1 X-512.00 Y384.00
M300 S30 (pen down)
G4 P150 (wait 150ms)
G1 X512.00 Y384.00
G1 X512.00 Y-384.00
G1 X-512.00 Y-384.00
G1 X-512.00 Y384.00
M300 S50 (pen up)
G4 P150 (wait 150ms)


(end of print job)
M300 S50 (pen up)
G4 P150 (wait 150ms)
M91 
G1 X0 Y0 F3500.00
G1 Z0.00 F150.00 (go up to finished level)
G1 X0.00 Y0.00 F3500.00 (go home)
M18 (drives off)

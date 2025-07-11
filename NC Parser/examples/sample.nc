
; Sample NC file for testing
; Simple rectangular pocket
G90 ; Absolute positioning
G21 ; Metric units
G17 ; XY plane
M03 S1000 ; Spindle on clockwise

; Rapid to start position
G00 X0 Y0 Z5
G00 Z1

; Plunge to cutting depth
G01 Z-2 F100

; Rectangular pocket (20x10mm)
G01 X20 Y0 F200
G01 X20 Y10
G01 X0 Y10
G01 X0 Y0

; Inner rectangle
G01 X5 Y2.5
G01 X15 Y2.5
G01 X15 Y7.5
G01 X5 Y7.5
G01 X5 Y2.5

; Circular interpolation example
G02 X10 Y5 I5 J2.5

; Retract
G00 Z5

; Spindle off and end
M05
M30

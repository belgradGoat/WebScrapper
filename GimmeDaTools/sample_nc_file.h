; Sample Heidenhain NC program for testing cycle time calculation
; Simple rectangular pocket milling operation

BEGIN PGM SAMPLE MM

BLK FORM 0.1 Z X+0 Y+0 Z-20
BLK FORM 0.2 X+100 Y+50 Z+0

TOOL CALL 10 Z S2000 F500

L Z+50 FMAX
L X+10 Y+10 FMAX
L Z+5 F800
L Z-2 F300

; Rough pocket
L X+90 F1200
L Y+40
L X+10
L Y+10
L Z-4 F300

; Another tool change
TOOL CALL 6 Z S3000 F800

L Z+5 FMAX
L X+10 Y+10 FMAX
L Z-2 F500

; Finish pass
L X+90 F600
L Y+40 F600
L X+10 F600
L Y+10 F600

L Z+50 FMAX

DWELL F2.5

END PGM SAMPLE MM
; [label] start
ldi r17, 255
ldi r18, 5
ldi r19, 3
ldi r20, 6
push r18
push r19
push r20

push r20
cal 14 ; [ref] times two
pop r21

pop r20
pop r19
pop r18

; [label] times two
pop r30
pop r19
add r19, r19
push r19
push r30
ret

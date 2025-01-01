A = eye(3);
B = ones(3);
C = A .+ B;
print C;

D = eye(3, 4);
D[0, 0] = 42;
D[0, 1] += 3;
D[2] += [1,2,3,4];
D[:, 1] += [1,2,3];
#D[1:3, 2:4] = 7; # opcjonalnie dla zainteresowanych
print D;
print D[2];
print D[2, 1];

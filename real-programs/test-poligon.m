test = "my test string";
message = "this is text";
print test;
print test, message;

a = 3;
print a;
a = -a;

vec1 = [-1, 2, 3];
vec1[1] *= 2.5;
print vec1;

M = [[-1, 2, -3], [4, -5, 6]];
print M;
print -M;
print M'; #' this comment is here to fix syntax highlighting as ' is treated like string #'

print M[1];
print M[0, 2];

rows = 2 + 3;
cols = 2;
A = ones(rows, cols);
B = eye(5,2);
C = A .+ B;
D = eye(7,2);

C = A .+ D;

print C;

return M;

print a;

return a;

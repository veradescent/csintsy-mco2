% Rules
parent(X, Y) :- father(X, Y), male(X).
parent(X, Y) :- mother(X, Y), female(X).

child(Y, X) :- parent(X, Y).

son(X, Y) :- child(X, Y), male(X).
daughter(X, Y) :- child(X, Y), female(X).

sibling(X, Y) :- parent(Z, X), parent(Z, Y), X \= Y.

brother(X, Y) :- sibling(X, Y), male(X).
sister(X, Y) :- sibling(X, Y), female(X).

grandparent(X, Y) :- parent(X, Z), parent(Z, Y).

grandfather(X, Y) :- grandparent(X, Y), male(X).

grandmother(X, Y) :- grandparent(X, Y), female(X).

grandchild(Y, X) :- grandparent(X, Y).

uncle(X, Y) :- sibling(X, Z), parent(Z, Y), male(X).

aunt(X, Y) :- sibling(X, Z), parent(Z, Y), female(X).

nephew(X, Y) :- parent(Z, X), sibling(Y, Z), male(X).

niece(X, Y) :- parent(Z, X), sibling(Y, Z), female(X).

cousin(X, Y) :- parent(A, X), parent(B, Y), sibling(A, B), X \= Y.

relative(X, Y) :- parent(X, Y); parent(Y, X); child(X, Y); child(Y, X); sibling(X, Y); sibling(Y, X);
grandparent(X, Y); grandparent(Y, X); grandchild(X, Y); grandchild(Y, X); aunt(X, Y); aunt(Y, X);
uncle(X, Y); uncle(Y, X); cousin(X, Y); cousin(Y, X); nephew(X, Y); nephew(Y, X); niece(X, Y);
niece(Y, X).  
% Revised Rules

% Father-mother-child relationship
father_of(X, Y) :- parent_of(X, Y), male(X). % If X is a parent and is male, then X is the father of Y.
mother_of(X, Y) :- parent_of(X, Y), female(X). % If X is a parent and is female, then X is the mother of Y.

child_of(Y, X) :- parent_of(X, Y).

% Gender-specific
son_of(Y, X) :- child_of(Y, X), male(Y).
daughter_of(Y, X) :- child_of(Y, X), female(Y).

% Sibling relationships
sibling_of(X, Y) :- parent_of(Z, X), parent_of(Z, Y), X \= Y. % If Z is a parent of both X and Y and X is not Y, then X and Y are siblings.

% Gender-specific
brother_of(X, Y) :- sibling_of(X, Y), male(X).
sister_of(X, Y) :- sibling_of(X, Y), female(X).

% Grandparent relationships
grandparent_of(X, Y) :- parent_of(X, Z), parent_of(Z, Y). % If X is a parent of Z and Z is a parent of Y, then X is a grandparent of Y.
grandchild_of(Y, X) :- grandparent_of(X, Y).

% Gender-specific
grandfather_of(X, Y) :- grandparent_of(X, Y), male(X).
grandmother_of(X, Y) :- grandparent_of(X, Y), female(X).

% Uncle and aunt relationships
uncle_of(X, Y) :- parent_of(Z, Y), sibling_of(X, Z), male(X).
aunt_of(X, Y) :- parent_of(Z, Y), sibling_of(X, Z), female(X).

nephew_of(Y, X) :- parent_of(Z, Y), sibling_of(X, Z), male(Y). % If Z is a parent of Y and sibling of X and Y is male, then Y is the nephew of X
niece_of(Y, X) :- parent_of(Z, Y), sibling_of(X, Z), female(Y). % If Z is a parent of Y and sibling of X and Y is female, then Y is the niece of X

% Cousin relationships
cousin_of(X, Y) :- parent_of(A, X), parent_of(B, Y), sibling_of(A, B), X \= Y.

% Relative relationships
relative(X, Y) :- parent(X, Y); parent(Y, X); child(X, Y); child(Y, X); sibling(X, Y); sibling(Y, X);
grandparent(X, Y); grandparent(Y, X); grandchild(X, Y); grandchild(Y, X); aunt(X, Y); aunt(Y, X);
uncle(X, Y); uncle(Y, X); cousin(X, Y); cousin(Y, X); nephew(X, Y); nephew(Y, X); niece(X, Y);
niece(Y, X).
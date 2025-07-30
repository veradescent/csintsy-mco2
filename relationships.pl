% Family Relationship Rules with Validation

% Basic parent-child relationship - this is a fact, not a rule
% parent_of(X, Y) facts will be added by the chatbot

% Father-mother-child relationship
father_of(X, Y) :- parent_of(X, Y), male(X), X \= Y. % If X is a parent and is male, then X is the father of Y.
mother_of(X, Y) :- parent_of(X, Y), female(X), X \= Y. % If X is a parent and is female, then X is the mother of Y.

child_of(Y, X) :- parent_of(X, Y), X \= Y.

% Gender-specific
son_of(Y, X) :- child_of(Y, X), male(Y).
daughter_of(Y, X) :- child_of(Y, X), female(Y).

% Sibling relationships
sibling_of(X, Y) :- parent_of(Z, X), parent_of(Z, Y), X \= Y, Z \= X, Z \= Y. % If Z is a parent of both X and Y and X is not Y, then X and Y are siblings.

% Gender-specific
brother_of(X, Y) :- sibling_of(X, Y), male(X).
sister_of(X, Y) :- sibling_of(X, Y), female(X).

% Half-sibling relationships (share one parent)
half_sibling_of(X, Y) :- parent_of(Z, X), parent_of(Z, Y), parent_of(W, X), parent_of(W, Y), Z \= W, X \= Y, Z \= X, Z \= Y, W \= X, W \= Y.

% Gender-specific half-siblings
half_brother_of(X, Y) :- half_sibling_of(X, Y), male(X).
half_sister_of(X, Y) :- half_sibling_of(X, Y), female(X).

% Step relationships
% Step-parent: married to a parent but not biologically related
stepfather_of(X, Y) :- parent_of(Z, Y), male(X), X \= Z, X \= Y, Z \= Y.
stepmother_of(X, Y) :- parent_of(Z, Y), female(X), X \= Z, X \= Y, Z \= Y.

% Step-siblings: children of step-parents
stepbrother_of(X, Y) :- stepfather_of(Z, X), stepfather_of(Z, Y), male(X), X \= Y.
stepsister_of(X, Y) :- stepfather_of(Z, X), stepfather_of(Z, Y), female(X), X \= Y.
stepbrother_of(X, Y) :- stepmother_of(Z, X), stepmother_of(Z, Y), male(X), X \= Y.
stepsister_of(X, Y) :- stepmother_of(Z, X), stepmother_of(Z, Y), female(X), X \= Y.

% Grandparent relationships
grandparent_of(X, Y) :- parent_of(X, Z), parent_of(Z, Y), X \= Y, Z \= X, Z \= Y. % If X is a parent of Z and Z is a parent of Y, then X is a grandparent of Y.
grandchild_of(Y, X) :- grandparent_of(X, Y).

% Gender-specific
grandfather_of(X, Y) :- grandparent_of(X, Y), male(X).
grandmother_of(X, Y) :- grandparent_of(X, Y), female(X).

% Gender-specific grandchildren
granddaughter_of(Y, X) :- grandchild_of(Y, X), female(Y).
grandson_of(Y, X) :- grandchild_of(Y, X), male(Y).

% Step-child relationships
stepchild_of(Y, X) :- stepfather_of(X, Y).
stepchild_of(Y, X) :- stepmother_of(X, Y).

% Uncle and aunt relationships
uncle_of(X, Y) :- parent_of(Z, Y), sibling_of(X, Z), male(X), X \= Y.
aunt_of(X, Y) :- parent_of(Z, Y), sibling_of(X, Z), female(X), X \= Y.

nephew_of(Y, X) :- parent_of(Z, Y), sibling_of(X, Z), male(Y), X \= Y. % If Z is a parent of Y and sibling of X and Y is male, then Y is the nephew of X
niece_of(Y, X) :- parent_of(Z, Y), sibling_of(X, Z), female(Y), X \= Y. % If Z is a parent of Y and sibling of X and Y is female, then Y is the niece of X

% Cousin relationships
cousin_of(X, Y) :- parent_of(A, X), parent_of(B, Y), sibling_of(A, B), X \= Y, A \= B.

% In-law relationships
% Mother-in-law: mother of spouse
mother_in_law_of(X, Y) :- parent_of(X, Z), female(X), X \= Y, Z \= Y.
% Father-in-law: father of spouse
father_in_law_of(X, Y) :- parent_of(X, Z), male(X), X \= Y, Z \= Y.

% Sister-in-law: sister of spouse
sister_in_law_of(X, Y) :- sibling_of(X, Z), female(X), X \= Y, Z \= Y.
% Brother-in-law: brother of spouse
brother_in_law_of(X, Y) :- sibling_of(X, Z), male(X), X \= Y, Z \= Y.

% Daughter-in-law: wife of son
daughter_in_law_of(X, Y) :- child_of(Z, Y), female(X), X \= Y, Z \= Y.
% Son-in-law: husband of daughter
son_in_law_of(X, Y) :- child_of(Z, Y), male(X), X \= Y, Z \= Y.

% Relative relationships
relative(X, Y) :- parent_of(X, Y); parent_of(Y, X); child_of(X, Y); child_of(Y, X); sibling_of(X, Y); sibling_of(Y, X);
grandparent_of(X, Y); grandparent_of(Y, X); grandchild_of(X, Y); grandchild_of(Y, X); aunt_of(X, Y); aunt_of(Y, X);
uncle_of(X, Y); uncle_of(Y, X); cousin_of(X, Y); cousin_of(Y, X); nephew_of(X, Y); nephew_of(Y, X); niece_of(X, Y);
niece_of(Y, X); half_sibling_of(X, Y); half_sibling_of(Y, X); stepfather_of(X, Y); stepmother_of(X, Y);
stepbrother_of(X, Y); stepsister_of(X, Y); mother_in_law_of(X, Y); father_in_law_of(X, Y);
sister_in_law_of(X, Y); brother_in_law_of(X, Y); daughter_in_law_of(X, Y); son_in_law_of(X, Y).

% Validation rules to prevent impossible relationships
% A person cannot be their own relative (except for the reflexive case)

% Circular relationships are impossible
impossible_circular(X, Y) :- parent_of(X, Y), parent_of(Y, X).
impossible_circular(X, Y) :- parent_of(X, Y), grandparent_of(Y, X).

% Incestual relationships are impossible
incestual_sibling_parent(X, Y) :- sibling_of(X, Y), parent_of(X, Y).
incestual_sibling_parent(X, Y) :- sibling_of(X, Y), parent_of(Y, X).

incestual_cousin_parent(X, Y) :- cousin_of(X, Y), parent_of(X, Y).
incestual_cousin_parent(X, Y) :- cousin_of(X, Y), parent_of(Y, X).

incestual_aunt_nephew_parent(X, Y) :- aunt_of(X, Y), parent_of(X, Y).
incestual_aunt_nephew_parent(X, Y) :- nephew_of(X, Y), parent_of(X, Y).

incestual_uncle_niece_parent(X, Y) :- uncle_of(X, Y), parent_of(X, Y).
incestual_uncle_niece_parent(X, Y) :- niece_of(X, Y), parent_of(X, Y).

% Impossible family structures
impossible_grandparent_sibling(X, Y) :- grandparent_of(X, Y), sibling_of(X, Y).
impossible_grandparent_sibling(X, Y) :- grandparent_of(Y, X), sibling_of(X, Y).

parent_of(mike, blake).
male(blake).
sibling_of(john, mike).
male(john).
% Family Relationship Rules

% Basic parent-child relationship - this is a fact, not a rule
% parent_of(X, Y) facts will be added by the chatbot

% Father-mother-child relationship
father_of(X, Y) :- parent_of(X, Y), male(X), X \= Y.
mother_of(X, Y) :- parent_of(X, Y), female(X), X \= Y.

child_of(Y, X) :- parent_of(X, Y), X \= Y.

% Gender-specific
son_of(Y, X) :- child_of(Y, X), male(Y).
daughter_of(Y, X) :- child_of(Y, X), female(Y).

% Sibling relationships (general - includes both full and half siblings)
sibling_of(X, Y) :- parent_of(Z, X), parent_of(Z, Y), X \= Y, Z \= X, Z \= Y.

% Gender-specific
brother_of(X, Y) :- sibling_of(X, Y), male(X).
sister_of(X, Y) :- sibling_of(X, Y), female(X).

% Extended family relationships
grandparent_of(X, Y) :- parent_of(X, Z), parent_of(Z, Y), X \= Y.
grandmother_of(X, Y) :- grandparent_of(X, Y), female(X).
grandfather_of(X, Y) :- grandparent_of(X, Y), male(X).

grandchild_of(Y, X) :- grandparent_of(X, Y), X \= Y.
granddaughter_of(Y, X) :- grandchild_of(Y, X), female(Y).
grandson_of(Y, X) :- grandchild_of(Y, X), male(Y).

% Uncle/Aunt relationships
uncle_of(X, Y) :- brother_of(X, Z), parent_of(Z, Y), X \= Y.
aunt_of(X, Y) :- sister_of(X, Z), parent_of(Z, Y), X \= Y.

% Niece/Nephew relationships
niece_of(Y, X) :- female(Y), (uncle_of(X, Y); aunt_of(X, Y)), X \= Y.
nephew_of(Y, X) :- male(Y), (uncle_of(X, Y); aunt_of(X, Y)), X \= Y.

% Alternative nephew/niece definitions that don't require parent gender
nephew_of(Y, X) :- male(Y), sibling_of(X, Z), parent_of(Z, Y), X \= Y.
niece_of(Y, X) :- female(Y), sibling_of(X, Z), parent_of(Z, Y), X \= Y.

% Cousin relationships
cousin_of(X, Y) :- parent_of(Z1, X), parent_of(Z2, Y), sibling_of(Z1, Z2), X \= Y.

% Half-sibling relationships
half_sibling_of(X, Y) :- 
    parent_of(Z, X), parent_of(Z, Y), X \= Y,  % Share one parent Z
    parent_of(W1, X), parent_of(W2, Y),        % Have other parents W1 and W2
    W1 \= W2, W1 \= Z, W2 \= Z.                % Other parents are different and not the shared parent
half_brother_of(X, Y) :- half_sibling_of(X, Y), male(X).
half_sister_of(X, Y) :- half_sibling_of(X, Y), female(X).



% Relative relationships
relative(X, Y) :- parent_of(X, Y); parent_of(Y, X); child_of(X, Y); child_of(Y, X); 
                  sibling_of(X, Y); sibling_of(Y, X); grandparent_of(X, Y); grandparent_of(Y, X);
                  uncle_of(X, Y); uncle_of(Y, X); aunt_of(X, Y); aunt_of(Y, X);
                  cousin_of(X, Y); cousin_of(Y, X); half_sibling_of(X, Y); half_sibling_of(Y, X).

% Ancestor-descendant relationships for cycle detection
ancestor_of(X, Y) :- parent_of(X, Y).
ancestor_of(X, Y) :- parent_of(X, Z), parent_of(Z, Y), X \= Y.
ancestor_of(X, Y) :- parent_of(X, Z1), parent_of(Z1, Z2), parent_of(Z2, Y), X \= Y, Z1 \= Y.

% Validation rules
impossible_circular(X, Y) :- parent_of(X, Y), parent_of(Y, X).
incestual_sibling_parent(X, Y) :- sibling_of(X, Y), parent_of(X, Y).
incestual_sibling_parent(X, Y) :- sibling_of(X, Y), parent_of(Y, X).

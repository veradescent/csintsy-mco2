% Discontiguous declarations to suppress warnings
:- discontiguous parent_of/2.
:- discontiguous male/1.
:- discontiguous female/1.
:- discontiguous sibling_of/2.
:- discontiguous half_sibling_of/2.
:- discontiguous brother_of/2.
:- discontiguous sister_of/2.
:- discontiguous uncle_of/2.
:- discontiguous aunt_of/2.
:- discontiguous niece_of/2.
:- discontiguous nephew_of/2.
:- discontiguous cousin_of/2.
:- discontiguous relative/2.
:- discontiguous ancestor_of/2.
:- discontiguous grandparent_of/2.
:- discontiguous grandchild_of/2.
:- discontiguous grandmother_of/2.
:- discontiguous grandfather_of/2.
:- discontiguous granddaughter_of/2.
:- discontiguous grandson_of/2.
:- discontiguous father_of/2.
:- discontiguous mother_of/2.
:- discontiguous child_of/2.
:- discontiguous son_of/2.
:- discontiguous daughter_of/2.
:- discontiguous half_brother_of/2.
:- discontiguous half_sister_of/2.
:- discontiguous impossible_circular/2.
:- discontiguous incestual_sibling_parent/2.

% ========================================
% Basic Parent-Child Relationships
% ========================================
father_of(X, Y) :- parent_of(X, Y), male(X), X \= Y.
mother_of(X, Y) :- parent_of(X, Y), female(X), X \= Y.
child_of(Y, X) :- parent_of(X, Y), X \= Y.
son_of(Y, X) :- child_of(Y, X), male(Y).
daughter_of(Y, X) :- child_of(Y, X), female(Y).

% ========================================
% Sibling Relationships
% ========================================
sibling_of(X, Y) :- parent_of(Z, X), parent_of(Z, Y), X \= Y, Z \= X, Z \= Y.
brother_of(X, Y) :- sibling_of(X, Y), male(X).
sister_of(X, Y) :- sibling_of(X, Y), female(X).

% Half-sibling relationships
half_sibling_of(X, Y) :- parent_of(Z, X), parent_of(Z, Y), X \= Y, parent_of(W1, X), parent_of(W2, Y), W1 \= W2, W1 \= Z, W2 \= Z.
half_brother_of(X, Y) :- half_sibling_of(X, Y), male(X).
half_sister_of(X, Y) :- half_sibling_of(X, Y), female(X).

% ========================================
% Grandparent-Grandchild Relationships
% ========================================
grandparent_of(X, Y) :- parent_of(X, Z), parent_of(Z, Y), X \= Y.
grandmother_of(X, Y) :- grandparent_of(X, Y), female(X).
grandfather_of(X, Y) :- grandparent_of(X, Y), male(X).
grandchild_of(Y, X) :- grandparent_of(X, Y), X \= Y.
granddaughter_of(Y, X) :- grandchild_of(Y, X), female(Y).
grandson_of(Y, X) :- grandchild_of(Y, X), male(Y).

% ========================================
% Uncle/Aunt - Niece/Nephew Relationships
% ========================================
uncle_of(X, Y) :- brother_of(X, Z), parent_of(Z, Y), X \= Y.
aunt_of(X, Y) :- sister_of(X, Z), parent_of(Z, Y), X \= Y.
niece_of(Y, X) :- female(Y), uncle_of(X, Y), X \= Y.
niece_of(Y, X) :- female(Y), aunt_of(X, Y), X \= Y.
nephew_of(Y, X) :- male(Y), uncle_of(X, Y), X \= Y.
nephew_of(Y, X) :- male(Y), aunt_of(X, Y), X \= Y.

% ========================================
% Half-Sibling Uncle/Aunt Relationships
% ========================================
uncle_of(X, Y) :- half_brother_of(X, Z), parent_of(Z, Y), X \= Y.
aunt_of(X, Y) :- half_sister_of(X, Z), parent_of(Z, Y), X \= Y.

% ========================================
% Grandparent Inference from Uncle/Aunt
% ========================================
grandfather_of(X, Y) :- uncle_of(X, Z), parent_of(Z, Y), male(X), X \= Y.
grandmother_of(X, Y) :- aunt_of(X, Z), parent_of(Z, Y), female(X), X \= Y.

% ========================================
% Cousin Relationships
% ========================================
cousin_of(X, Y) :- parent_of(Z1, X), parent_of(Z2, Y), sibling_of(Z1, Z2), X \= Y.

% ========================================
% General Relative Relationships
% ========================================
relative(X, Y) :- parent_of(X, Y).
relative(X, Y) :- parent_of(Y, X).
relative(X, Y) :- child_of(X, Y).
relative(X, Y) :- child_of(Y, X).
relative(X, Y) :- sibling_of(X, Y).
relative(X, Y) :- sibling_of(Y, X).
relative(X, Y) :- grandparent_of(X, Y).
relative(X, Y) :- grandparent_of(Y, X).
relative(X, Y) :- uncle_of(X, Y).
relative(X, Y) :- uncle_of(Y, X).
relative(X, Y) :- aunt_of(X, Y).
relative(X, Y) :- aunt_of(Y, X).
relative(X, Y) :- cousin_of(X, Y).
relative(X, Y) :- cousin_of(Y, X).
relative(X, Y) :- half_sibling_of(X, Y).
relative(X, Y) :- half_sibling_of(Y, X).

% ========================================
% Ancestor-Descendant Relationships
% ========================================
ancestor_of(X, Y) :- parent_of(X, Y).
ancestor_of(X, Y) :- parent_of(X, Z), parent_of(Z, Y), X \= Y.
ancestor_of(X, Y) :- parent_of(X, Z1), parent_of(Z1, Z2), parent_of(Z2, Y), X \= Y, Z1 \= Y.

% ========================================
% Validation Rules (for detecting invalid relationships)
% ========================================
impossible_circular(X, Y) :- parent_of(X, Y), parent_of(Y, X).
incestual_sibling_parent(X, Y) :- sibling_of(X, Y), parent_of(X, Y).
incestual_sibling_parent(X, Y) :- sibling_of(X, Y), parent_of(Y, X).

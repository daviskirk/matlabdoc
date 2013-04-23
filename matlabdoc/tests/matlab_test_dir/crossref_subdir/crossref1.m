function [one, two] = crossref1(in1, in2)
%FNAME short summary
%
% [one, two] = fname(in1, in2)
%

l = in1 + in2 % comment here

something = crossref2(in1, in2)
somethingElse = crossref3(in1, in2) % with comment

recursive = crossref1(in1, in2)

% classdef SomeClass < T
% function in comment: function b = a(in)
% function c = b(in)

l = in1 + in2 % comment here
l(1) = 123 % variable call

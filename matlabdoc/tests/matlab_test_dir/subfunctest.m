function [one, two] = subfunctest(in1, in2)
%FNAME short summary
%
% [one, two] = fname(in1, in2)
%

l = in1 + in2 % comment here

% function in comment: function b = a(in)
% function c = b(in)

l = in1 + in2 % comment here
l(1) = 123 % variable call



function subfunc1(subin1)
% subdocstring1 one line and so on
%
% function subfun1(subin1)
% bla ...
a = 2
dosomething()

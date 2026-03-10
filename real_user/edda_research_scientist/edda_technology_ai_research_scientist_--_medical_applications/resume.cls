%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Medium Length Professional CV - RESUME CLASS FILE
% Adapted to tighten line spacing + improve grouping
% Only spacing fix for name and address insertion
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\ProvidesClass{resume}[2010/07/10 v0.9 Resume class with tighter spacing]

\LoadClass[11pt,letterpaper]{article}

\usepackage[parfill]{parskip}
\usepackage{array}
\usepackage{ifthen}
\usepackage{enumitem}

\pagestyle{empty}

%----------------------------------------------------------------------------------------
% Heading Commands
%----------------------------------------------------------------------------------------
\def \name#1{\def\@name{#1}}
\def \@name {}

\def \addressSep {\textbar}

\let \@addressone \relax
\let \@addresstwo \relax
\let \@addressthree \relax

\def \address #1{
  \@ifundefined{@addresstwo}{
    \def \@addresstwo {#1}
  }{
  \@ifundefined{@addressthree}{
  \def \@addressthree {#1}
  }{
     \def \@addressone {#1}
  }}
}

% Use spacing commands here for name and address
\def \printname {
  \begingroup
    \hfil{\namesize\bf \@name}\hfil
    \nameskip
    \break
  \endgroup
}

\def \printaddress #1{
  \begingroup
    \def \\ {\addressSep\ }
    \centerline{#1}
  \endgroup
  \addressskip
}

\let\ori@document=\document
\renewcommand{\document}{
  \ori@document
  \printname
  \@ifundefined{@addressone}{}{\printaddress{\@addressone}}
  \@ifundefined{@addresstwo}{}{\printaddress{\@addresstwo}}
  \@ifundefined{@addressthree}{}{\printaddress{\@addressthree}}
  \sectionlineskip
}

%----------------------------------------------------------------------------------------
% Section Formatting
%----------------------------------------------------------------------------------------

\newenvironment{rSection}[1]{
  \vspace{0.15em}
  \MakeUppercase{\bf #1}
  \vspace{0.15em}\\
  \hrule
  \vspace{-0.3em}
  \begin{list}{}{\setlength{\leftmargin}{0.6em}}
  \item[]
}{
  \end{list}
  \vspace{-0.2em}
}

%----------------------------------------------------------------------------------------
% Work/Education Subsection Formatting
%----------------------------------------------------------------------------------------

\newenvironment{rSubsection}[4]{
  {\bf #1} \hfill {#2} \\
  \ifthenelse{\equal{#3}{}}{}{%
    {\em #3 \hfill #4}%
  }\\[-2em]
  \begin{list}{$\cdot$}{%
    \setlength{\leftmargin}{1em}
    \setlength{\itemsep}{0pt}
    \setlength{\parsep}{0pt}
    \setlength{\topsep}{0pt}
    \setlength{\partopsep}{0pt}
  }
}{
  \end{list}
  \vspace{0.05em} % space after this entry
}

\newcommand{\certification}[4]{%
  \noindent
  {\bf #1} \hfill #2 \\[-0.3em]
  {\em #3 #4} \vspace{0.05em}
}


%----------------------------------------------------------------------------------------
% Global Spacing Customizations
%----------------------------------------------------------------------------------------

\def\namesize{\large}
\def\addressskip{\vspace{-2em}}   % reduced space after address
\def\sectionlineskip{\vspace{0.1em}}
\def\sectionskip{\vspace{0.1em}}

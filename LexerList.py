from PyQt5.Qsci import *

#Lexer,Language Name for Menu,Fileprefix, XML File
def getLexerList():
    lexerList = []
    lexerList.append([QsciLexerAVS,"AVS","",""])
    lexerList.append([QsciLexerBash,"Bash","sh",""])
    lexerList.append([QsciLexerBatch,"Batch","bat","batch"])
    lexerList.append([QsciLexerCMake,"CMake","cmake","cmake"])
    lexerList.append([QsciLexerCoffeeScript,"CoffeeScript","coffe","coffe"])
    lexerList.append([QsciLexerCPP,"C++","cpp","cpp"])
    lexerList.append([QsciLexerCSharp,"C#","cs",""])
    lexerList.append([QsciLexerIDL,"IDL","idl",""])
    lexerList.append([QsciLexerJava,"Java","java","java"])
    lexerList.append([QsciLexerJavaScript,"JavaScript","js","javascript"])
    lexerList.append([QsciLexerCSS,"CSS","css","css"])
    lexerList.append([QsciLexerD,"D","d",""])
    lexerList.append([QsciLexerDiff,"Diff","diff",""])
    lexerList.append([QsciLexerFortran,"Fortran","f90",""])
    lexerList.append([QsciLexerHTML,"HTML","html","html"])
    lexerList.append([QsciLexerXML,"XML","xml","xml"])
    lexerList.append([QsciLexerJSON,"JSON","json",""])
    lexerList.append([QsciLexerLua,"LUA","lua","lua"])
    lexerList.append([QsciLexerMakefile,"Makefile","am",""])
    lexerList.append([QsciLexerMarkdown,"Markdown","md",""])
    lexerList.append([QsciLexerMatlab,"Matlab","m",""])
    lexerList.append([QsciLexerOctave,"Octave","",""])
    lexerList.append([QsciLexerPascal,"Pascal","pp",""])
    lexerList.append([QsciLexerPerl,"Perl","pl","perl"])
    lexerList.append([QsciLexerPO,"PO","",""])
    lexerList.append([QsciLexerPostScript,"PostScript","",""])
    lexerList.append([QsciLexerProperties,"Properties","properties",""])
    lexerList.append([QsciLexerPython,"Python","py","python"])
    lexerList.append([QsciLexerRuby,"Ruby","rb",""])
    lexerList.append([QsciLexerSpice,"Spice","",""])
    lexerList.append([QsciLexerSQL,"SQL","",""])
    lexerList.append([QsciLexerTCL,"TCL","tcl",""])
    lexerList.append([QsciLexerTeX,"TeX","tex","tex"])
    lexerList.append([QsciLexerVerilog,"Verilog","",""])
    lexerList.append([QsciLexerVHDL,"VHDL","","vhdl"])
    lexerList.append([QsciLexerYAML,"YAML","yml",""])
    return lexerList

<?xml version="1.0" encoding="ascii"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-US" lang="en-US">
<head>
<link rel="icon" href="/furbani/ns-3-dce/static/hgicon.png" type="image/png" />
<meta name="robots" content="index, nofollow"/>
<link rel="stylesheet" href="/furbani/ns-3-dce/static/style-gitweb.css" type="text/css" />


<title>furbani/ns-3-dce: utils/clone_and_compile_ns3_dce.sh@60a9cf52e24a</title>
<link rel="alternate" type="application/atom+xml"
   href="/furbani/ns-3-dce/atom-log" title="Atom feed for furbani/ns-3-dce"/>
<link rel="alternate" type="application/rss+xml"
   href="/furbani/ns-3-dce/rss-log" title="RSS feed for furbani/ns-3-dce"/>
</head>
<body>

<div class="page_header">
<a href="http://mercurial.selenic.com/" title="Mercurial" style="float: right;">Mercurial</a><a href="/furbani/ns-3-dce/summary">furbani/ns-3-dce</a> / file revision
</div>

<div class="page_nav">
<a href="/furbani/ns-3-dce/summary">summary</a> |
<a href="/furbani/ns-3-dce/shortlog">shortlog</a> |
<a href="/furbani/ns-3-dce/log">changelog</a> |
<a href="/furbani/ns-3-dce/graph">graph</a> |
<a href="/furbani/ns-3-dce/tags">tags</a> |
<a href="/furbani/ns-3-dce/branches">branches</a> |
<a href="/furbani/ns-3-dce/file/60a9cf52e24a/utils/">files</a> |
<a href="/furbani/ns-3-dce/rev/60a9cf52e24a">changeset</a> |
file |
<a href="/furbani/ns-3-dce/file/tip/utils/clone_and_compile_ns3_dce.sh">latest</a> |
<a href="/furbani/ns-3-dce/log/60a9cf52e24a/utils/clone_and_compile_ns3_dce.sh">revisions</a> |
<a href="/furbani/ns-3-dce/annotate/60a9cf52e24a/utils/clone_and_compile_ns3_dce.sh">annotate</a> |
<a href="/furbani/ns-3-dce/diff/60a9cf52e24a/utils/clone_and_compile_ns3_dce.sh">diff</a> |
<a href="/furbani/ns-3-dce/raw-file/60a9cf52e24a/utils/clone_and_compile_ns3_dce.sh">raw</a> |
<a href="/furbani/ns-3-dce/help">help</a>
<br/>
</div>

<div class="title">utils/clone_and_compile_ns3_dce.sh</div>

<div class="title_text">
<table cellspacing="0">
<tr>
 <td>author</td>
 <td>&#102;&#114;&#101;&#100;&#101;&#114;&#105;&#99;&#46;&#117;&#114;&#98;&#97;&#110;&#105;&#64;&#105;&#110;&#114;&#105;&#97;&#46;&#102;&#114;</td></tr>
<tr>
 <td></td>
 <td>Tue Dec 13 10:51:45 2011 +0100 (3 hours ago)</td></tr>

<tr>
 <td>changeset 204</td>
 <td style="font-family:monospace"><a class="list" href="/furbani/ns-3-dce/rev/60a9cf52e24a">60a9cf52e24a</a></td></tr>

<tr>
<td>parent 203</td>
<td style="font-family:monospace">
<a class="list" href="/furbani/ns-3-dce/file/84a1955f45cf/utils/clone_and_compile_ns3_dce.sh">
84a1955f45cf
</a>
</td>
</tr>

<tr>
 <td>permissions</td>
 <td style="font-family:monospace">-rwxr-xr-x</td></tr>
</table>
</div>

<div class="page_path">
Fix kernel mode and tests.
</div>

<div class="page_body">

<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l1" id="l1">     1</a> #!/bin/bash
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l2" id="l2">     2</a> # this script checkout NS3 and DCE sources, and build them.
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l3" id="l3">     3</a> USE_KERNEL=NO
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l4" id="l4">     4</a> cd `dirname $BASH_SOURCE`/../..
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l5" id="l5">     5</a> SAVE_PATH=$PATH
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l6" id="l6">     6</a> SAVE_LDLP=$LD_LIBRARY_PATH
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l7" id="l7">     7</a> SAVE_PKG=$PKG_CONFIG_PATH
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l8" id="l8">     8</a> #echo clone ns-3-dce : 
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l9" id="l9">     9</a> #hg clone http://code.nsnam.org/furbani/ns-3-dce
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l10" id="l10">    10</a> echo clone readversiondef
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l11" id="l11">    11</a> hg clone http://code.nsnam.org/mathieu/readversiondef
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l12" id="l12">    12</a> if [ &quot;YES&quot; == &quot;$USE_KERNEL&quot; ]
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l13" id="l13">    13</a> then
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l14" id="l14">    14</a> 	echo clone ns-3-linux
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l15" id="l15">    15</a>  	hg clone http://code.nsnam.org/furbani/ns-3-linux
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l16" id="l16">    16</a> fi	
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l17" id="l17">    17</a> echo clone ns-3-dev
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l18" id="l18">    18</a> hg clone http://code.nsnam.org/ns-3-dev -r 027aae146ae2
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l19" id="l19">    19</a> mkdir build
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l20" id="l20">    20</a> cd ns-3-dev
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l21" id="l21">    21</a> patch -p1 &lt;../ns-3-dce/utils/packet-socket-upgrade-exp.patch
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l22" id="l22">    22</a> patch -p1 &lt;../ns-3-dce/utils/0001-Replace-references-to-m_recvpktinfo-with-method-call.patch
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l23" id="l23">    23</a> patch -p1 &lt;../ns-3-dce/utils/0002-A-new-templated-static-method-Ipv4RoutingHelper-GetR.patch
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l24" id="l24">    24</a> ./waf configure --prefix=`pwd`/../build --enable-tests
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l25" id="l25">    25</a> ./waf
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l26" id="l26">    26</a> ./waf install
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l27" id="l27">    27</a> cd ..
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l28" id="l28">    28</a> export PATH=$SAVE_PATH:`pwd`/build/bin
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l29" id="l29">    29</a> export LD_LIBRARY_PATH=$SAVE_LDLP:`pwd`/build/lib
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l30" id="l30">    30</a> export PKG_CONFIG_PATH=$SAVE_PKG:`pwd`/build/lib/pkgconfig
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l31" id="l31">    31</a> cd readversiondef/
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l32" id="l32">    32</a> make 
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l33" id="l33">    33</a> make install PREFIX=`pwd`/../build/
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l34" id="l34">    34</a> cd ..
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l35" id="l35">    35</a> if [ &quot;YES&quot; == &quot;$USE_KERNEL&quot; ]
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l36" id="l36">    36</a> then
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l37" id="l37">    37</a> 	cd ns-3-linux/
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l38" id="l38">    38</a> # 	git clone git://git.kernel.org/pub/scm/linux/kernel/git/davem/net-next-2.6.git net-next-2.6
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l39" id="l39">    39</a>  	git clone git://git.kernel.org/pub/scm/linux/kernel/git/davem/net-next.git net-next-2.6
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l40" id="l40">    40</a> 	make unpatch
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l41" id="l41">    41</a> 	make  setup
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l42" id="l42">    42</a> 	make defconfig
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l43" id="l43">    43</a> 	make config
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l44" id="l44">    44</a> 	sed s/CONFIG_PACKET=m/CONFIG_PACKET=y/ config &gt;c2
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l45" id="l45">    45</a> 	rm config
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l46" id="l46">    46</a> 	mv c2 config
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l47" id="l47">    47</a> 	make
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l48" id="l48">    48</a> 	cd ..
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l49" id="l49">    49</a> #	wget http://devresources.linuxfoundation.org/dev/iproute2/download/iproute2-2.6.33.tar.bz2
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l50" id="l50">    50</a> 	wget http://www.linuxgrill.com/anonymous/iproute2/NEW-OSDL/iproute2-2.6.38.tar.bz2     
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l51" id="l51">    51</a> #	tar jxf iproute2-2.6.33.tar.bz2
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l52" id="l52">    52</a> 	tar jxf iproute2-2.6.38.tar.bz2
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l53" id="l53">    53</a> #	cd iproute2-2.6.33
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l54" id="l54">    54</a> 	cd iproute2-2.6.38
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l55" id="l55">    55</a> 	./configure
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l56" id="l56">    56</a> 	LDFLAGS=-pie make CCOPTS='-fpic -D_GNU_SOURCE -O0 -U_FORTIFY_SOURCE'
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l57" id="l57">    57</a> 	cd ../ns-3-dce
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l58" id="l58">    58</a> 	mkdir -p build/bin_dce
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l59" id="l59">    59</a> 	cd  build/bin_dce
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l60" id="l60">    60</a> 	ln -s ../../../ns-3-linux/libnet-next-2.6.so
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l61" id="l61">    61</a> #	ln -s ../iproute2-2.6.33/ip/ip
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l62" id="l62">    62</a> 	ln -s ../../../iproute2-2.6.38/ip/ip
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l63" id="l63">    63</a> 	cd ../../example/ccnx
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l64" id="l64">    64</a> 	ln -s ../../build/bin_dce/libnet-next-2.6.so
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l65" id="l65">    65</a> #	ln -s ../../ip
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l66" id="l66">    66</a> 	cd ../..
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l67" id="l67">    67</a> fi
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l68" id="l68">    68</a> cd ns-3-dce/
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l69" id="l69">    69</a> if [ &quot;YES&quot; == &quot;$USE_KERNEL&quot; ]
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l70" id="l70">    70</a> then
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l71" id="l71">    71</a>     WAF_KERNEL=--enable-kernel-stack=`pwd`/../ns-3-linux
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l72" id="l72">    72</a> fi
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l73" id="l73">    73</a> ./waf configure --prefix=`pwd`/../build --verbose $WAF_KERNEL
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l74" id="l74">    74</a> ./waf
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l75" id="l75">    75</a> ./waf install
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l76" id="l76">    76</a> export LD_LIBRARY_PATH=$SAVE_LDLP:`pwd`/build/lib:`pwd`/build/bin:`pwd`/../build/lib
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l77" id="l77">    77</a> . utils/setenv.sh
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l78" id="l78">    78</a> echo Launch NS3TEST-DCE
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l79" id="l79">    79</a> ./build/bin/ns3test-dce --verbose
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l80" id="l80">    80</a> 
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l81" id="l81">    81</a> 
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l82" id="l82">    82</a> 
</pre>
</div>
<div style="font-family:monospace" class="parity0">
<pre><a class="linenr" href="#l83" id="l83">    83</a> 
</pre>
</div>
<div style="font-family:monospace" class="parity1">
<pre><a class="linenr" href="#l84" id="l84">    84</a> 
</pre>
</div>
</div>

<div class="page_footer">
<div class="page_footer_text">furbani/ns-3-dce</div>
<div class="rss_logo">
<a href="/furbani/ns-3-dce/rss-log">RSS</a>
<a href="/furbani/ns-3-dce/atom-log">Atom</a>
</div>
<br />

</div>
</body>
</html>


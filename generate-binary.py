#!/usr/bin/env python

def collect_source(source):
    import os
    sources = []
    for root, dirs, files in os.walk(source):
        for f in files:
            if f.endswith('.py'):
                sources.append(os.path.join(root, f))
    return sources

def calculate_hash(sources):
    import hashlib
    m = hashlib.md5()
    for source in sources:
        f = open(source, 'r')
        for line in f:
            m.update(line)
        f.close()
    md5hash = m.hexdigest()
    return md5hash

def generate_zip(sources):
    import zipfile
    import tempfile
    import os
    (handle, pathname) = tempfile.mkstemp()
    f = zipfile.ZipFile(pathname, 'w')
    for source in sources:
        f.write(source)
    f.close()
    os.close(handle)
    return pathname

def generate_binary(source_dir, output):
    import base64
    import StringIO
    sources = collect_source(source_dir)
    sources_md5 = calculate_hash(sources)
    zipfile = generate_zip(sources)
    zipdata = StringIO.StringIO()
    base64.encode(open(zipfile, 'r'), zipdata)
    
    f = open(output, 'w')
    f.write("""#!/usr/bin/env python
sources = [%s]
sources_md5 = "%s"
zipdata = \"\"\"%s\"\"\"

def decompress(output):
    import StringIO
    import zipfile
    import base64
    decoded = StringIO.StringIO()
    base64.decode(StringIO.StringIO(zipdata), decoded)
    f = zipfile.ZipFile(decoded, 'r')
    f.extractall(pathname)
    f.close()
    

import os
import sys
pathname = os.path.join('.bake', sources_md5)
if not os.path.exists(pathname):
    os.makedirs(pathname)
    decompress(pathname)
elif not os.path.isdir(pathname):
    import tempfile
    pathname = tempfile.mkdtemp()
    decompress(pathname)
sys.path.append(pathname)
import %s as source
source.main(sys.argv)

""" % (','.join(["'%s'" % source for source in sources]), sources_md5, zipdata.getvalue(),
       source_dir))
    f.close()

if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('-s', '--source', dest='source', type='string', action='store', default='bake',
                      help='Source directory to embedd')
    parser.add_option('-o', '--output', dest='output', type='string', action='store', default='bake.binary',
                      help='Executable to generate')
    (options, args) = parser.parse_args()
    generate_binary(options.source, options.output)
    


    



import unittest
import bake.Utils


class TestModuleUtils(unittest.TestCase):
    """Tests cases for the Utils Class."""
    
    def setUp(self):
        """Common set Up environment, available for all tests."""
        
    def tearDown(self):
        """Cleans the environment environment for the next tests."""

   
    def test_split_args(self):
        """Tests the split_args method of Class Utils. """
        
        string = "CCOPTS='-fpic -D_GNU_SOURCE -O0 -U_FORTIFY_SOURCE'"
        testResult = bake.Utils.split_args(string)
        self.assertTrue(len(testResult)==1)
        self.assertEqual(testResult[0], 
                         "CCOPTS='-fpic -D_GNU_SOURCE -O0 -U_FORTIFY_SOURCE'")
        
        string = "CCOPTS='-fpic -D_GNU_SOURCE -O0 -U_FORTIFY_SOURCE' -g"
        testResult = bake.Utils.split_args(string)
        self.assertTrue(len(testResult)==2)
        self.assertEqual(testResult[0], 
                         "CCOPTS='-fpic -D_GNU_SOURCE -O0 -U_FORTIFY_SOURCE'")
        self.assertEqual(testResult[1], "-g")

        string = "CCOPTS=-fpic -D_GNU_SOURCE -O0 -U_FORTIFY_SOURCE -g"
        testResult = bake.Utils.split_args(string)
        self.assertTrue(len(testResult)==5)
        self.assertEqual(testResult[0], "CCOPTS=-fpic")
        self.assertEqual(testResult[1], "-D_GNU_SOURCE")
        self.assertEqual(testResult[4], "-g")

        string = ""
        testResult = bake.Utils.split_args(string)
        self.assertTrue(len(testResult)==0)
        
        string = "install PREFIX=`pwd`/../build"
        testResult = bake.Utils.split_args(string)
        self.assertTrue(len(testResult)==2)
        self.assertEqual(testResult[0], "install")
        self.assertEqual(testResult[1], "PREFIX=`pwd`/../build")
        
        string = "install PREFIX='pwd'/../build -g"
        testResult = bake.Utils.split_args(string)
        self.assertTrue(len(testResult)==3)
        self.assertEqual(testResult[0], "install")
        self.assertEqual(testResult[1], "PREFIX='pwd'/../build")

        string = "'install PREFIX='pwd'/../build' -g"
        testResult = bake.Utils.split_args(string)
        self.assertTrue(len(testResult)==2)
        self.assertEqual(testResult[0], "'install PREFIX='pwd'/../build'")
        self.assertEqual(testResult[1], "-g")
        

# main call for the tests        
if __name__ == '__main__':
    unittest.main()

import unittest
from environment import strip_cpu,effective_environment,KEYS
class CpuRemovalTests(unittest.TestCase):
    def test_preserve_other_arguments(self):
        self.assertEqual(strip_cpu('-Xmx2g -XX:ActiveProcessorCount=1 --add-opens=java.base/java.lang=ALL-UNNAMED'),'-Xmx2g  --add-opens=java.base/java.lang=ALL-UNNAMED')
    def test_all_inheritance_paths(self):
        e=effective_environment({**{k:'-XX:ActiveProcessorCount=8 -Dkeep=yes' for k in KEYS},'PATH':'/bin'})
        for k in KEYS:self.assertNotIn('ActiveProcessorCount',e[k]);self.assertIn('-Dkeep=yes',e[k])
    def test_quotes_and_multiple(self):
        self.assertEqual(strip_cpu('"-XX:ActiveProcessorCount=1" -Xms32m -XX:ActiveProcessorCount=4'),'-Xms32m')
    def test_no_override_unchanged(self):
        self.assertEqual(strip_cpu('-Dpath="a b" -Xmx2g'),'-Dpath="a b" -Xmx2g')
    def test_unknown_syntax_fails_closed(self):
        with self.assertRaises(ValueError):effective_environment({'JAVA_TOOL_OPTIONS':'-XX:ActiveProcessorCount=wrong'})
if __name__=='__main__':unittest.main()

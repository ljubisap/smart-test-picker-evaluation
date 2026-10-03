import java.io.File;
import java.lang.reflect.Method;
Class<?> readerClass = Class.forName("com.sap.oss.smarttestpicker.mapper.CoverageMapReader");
Method loadMethod = readerClass.getMethod("load", File.class);
System.out.println("CODE_SOURCE\t" + readerClass.getProtectionDomain().getCodeSource().getLocation());
String root = "/Users/D061177/work/issta/smart-test-picker-evaluation/";
String[][] maps = {
  {"commons-lang", "commons-lang/results/test-coverage-map.json.gz"},
  {"jgrapht", "jgrapht/results/test-coverage-map.json.gz"},
  {"spring-core", "spring-core/results/test-coverage-map.json"},
  {"petclinic", "petclinic/results/test-coverage-map.json"},
  {"flink", "flink/results/test-coverage-map.json.gz"},
  {"spring-security", "spring-security/results/test-coverage-map.json.gz"},
  {"hibernate", "hibernate/results/test-coverage-map.json.gz"},
  {"quarkus", "quarkus/results/test-coverage-map.json.gz"}
};
for (String[] item : maps) {
  try {
    Object map = loadMethod.invoke(null, new File(root + item[1]));
    Method mappingsMethod = map.getClass().getMethod("getTestMappings");
    Method metadataMethod = map.getClass().getMethod("getMetadata");
    java.util.Map<?, ?> mappings = (java.util.Map<?, ?>) mappingsMethod.invoke(map);
    System.out.println("MAP_RESULT\t" + item[0] + "\tACCEPTED\t" + mappings.size() + "\t" + (metadataMethod.invoke(map) != null));
  } catch (Throwable error) {
    System.out.println("MAP_RESULT\t" + item[0] + "\tREJECTED\t" + error.getClass().getName() + ": " + error.getMessage());
  }
}
/exit

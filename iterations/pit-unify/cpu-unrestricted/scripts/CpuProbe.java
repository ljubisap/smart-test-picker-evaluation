import java.lang.management.ManagementFactory;
public class CpuProbe {
  public static void main(String[] args) {
    System.out.println("CONTROL_JVM_NOT_SUBJECT_TEST");
    System.out.println("availableProcessors=" + Runtime.getRuntime().availableProcessors());
    System.out.println("inputArguments=" + ManagementFactory.getRuntimeMXBean().getInputArguments());
    System.out.println("java.version=" + System.getProperty("java.version"));
    System.out.println("java.home=" + System.getProperty("java.home"));
  }
}

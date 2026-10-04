import com.google.gson.*;
import com.sap.oss.smarttestpicker.mapper.CoverageMap;
import com.sap.oss.smarttestpicker.mapper.CoverageMapReader;
import com.sap.oss.smarttestpicker.selector.SelectionResult;
import com.sap.oss.smarttestpicker.selector.TestSelector;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.GZIPInputStream;

public final class SelectorHarness {
  static Reader reader(Path path) throws IOException {
    InputStream in = Files.newInputStream(path);
    if (path.toString().endsWith(".gz")) in = new GZIPInputStream(in);
    return new InputStreamReader(in, StandardCharsets.UTF_8);
  }
  static List<String> normalized(JsonObject entry, String field) {
    if (!entry.has(field) || entry.get(field).isJsonNull()) return List.of();
    if (!entry.get(field).isJsonArray()) throw new IllegalArgumentException("non-list " + field);
    List<String> out = new ArrayList<>();
    for (JsonElement element : entry.getAsJsonArray(field)) out.add(element.getAsString());
    return out;
  }
  static String hash(List<String> values) throws Exception {
    MessageDigest digest = MessageDigest.getInstance("SHA-256");
    for (String value : values) {
      digest.update(value.getBytes(StandardCharsets.UTF_8)); digest.update((byte)0);
    }
    return HexFormat.of().formatHex(digest.digest());
  }
  public static void main(String[] args) throws Exception {
    Gson gson = new GsonBuilder().disableHtmlEscaping().create();
    JsonObject manifest;
    try (Reader input = Files.newBufferedReader(Path.of(args[0]))) {
      manifest = JsonParser.parseReader(input).getAsJsonObject();
    }
    JsonObject output = new JsonObject();
    output.addProperty("testSelectorCodeSource", TestSelector.class.getProtectionDomain().getCodeSource().getLocation().toString());
    output.addProperty("coverageMapReaderCodeSource", CoverageMapReader.class.getProtectionDomain().getCodeSource().getLocation().toString());
    JsonArray loaderRows = new JsonArray(); JsonArray caseRows = new JsonArray();
    TestSelector selector = new TestSelector();
    for (JsonElement mapElement : manifest.getAsJsonArray("maps")) {
      JsonObject mapSpec = mapElement.getAsJsonObject(); Path path = Path.of(mapSpec.get("path").getAsString());
      JsonObject raw;
      try (Reader input = reader(path)) { raw = JsonParser.parseReader(input).getAsJsonObject(); }
      JsonObject rawMappings = raw.getAsJsonObject("testMappings");
      CoverageMap loaded = CoverageMapReader.load(path.toFile());
      Map<String, Map<String, List<String>>> loadedMappings = loaded.getTestMappings();
      JsonArray differences = new JsonArray(); Set<String> rawU = new TreeSet<>(), loadedU = new TreeSet<>();
      Set<String> keys = new TreeSet<>(); keys.addAll(rawMappings.keySet()); keys.addAll(loadedMappings.keySet());
      for (String key : keys) {
        JsonObject rawEntry = rawMappings.has(key) ? rawMappings.getAsJsonObject(key) : new JsonObject();
        List<String> rawClasses=normalized(rawEntry,"classes"), rawMethods=normalized(rawEntry,"methods");
        Map<String,List<String>> loadedEntry=loadedMappings.get(key);
        List<String> loadedClasses=loadedEntry==null || loadedEntry.get("classes")==null ? List.of() : loadedEntry.get("classes");
        List<String> loadedMethods=loadedEntry==null || loadedEntry.get("methods")==null ? List.of() : loadedEntry.get("methods");
        if (rawClasses.isEmpty() && rawMethods.isEmpty()) rawU.add(key);
        if (loadedClasses.isEmpty() && loadedMethods.isEmpty()) loadedU.add(key);
        if (!rawClasses.equals(loadedClasses) || !rawMethods.equals(loadedMethods)) {
          JsonObject diff=new JsonObject(); diff.addProperty("test",key);
          diff.add("rawClasses",gson.toJsonTree(rawClasses)); diff.add("loadedClasses",gson.toJsonTree(loadedClasses));
          diff.add("rawMethods",gson.toJsonTree(rawMethods)); diff.add("loadedMethods",gson.toJsonTree(loadedMethods)); differences.add(diff);
        }
      }
      JsonObject loader=new JsonObject(); loader.addProperty("project",mapSpec.get("project").getAsString());
      loader.addProperty("rawEntries",rawMappings.size()); loader.addProperty("loadedEntries",loadedMappings.size());
      loader.addProperty("differentEntryCount",differences.size()); loader.add("differences",differences);
      loader.add("rawU",gson.toJsonTree(rawU)); loader.add("loadedU",gson.toJsonTree(loadedU)); loaderRows.add(loader);
      for (JsonElement caseElement : mapSpec.getAsJsonArray("cases")) {
        JsonObject spec=caseElement.getAsJsonObject(); String cls=spec.get("changedClass").getAsString(), method=spec.get("changedMethod").getAsString();
        SelectionResult result=selector.selectTests(path.toFile(),Set.of(cls),Set.of(cls+"#"+method));
        List<String> selected=new ArrayList<>(result.getSelectedTests()); Collections.sort(selected);
        JsonObject row=new JsonObject(); row.addProperty("caseId",spec.get("caseId").getAsString()); row.addProperty("project",mapSpec.get("project").getAsString());
        row.addProperty("mode",result.isFullSuiteRequired()?"FULL_SUITE":(selected.isEmpty()?"NONE":"SELECTED")); row.addProperty("reason",result.getReason());
        row.add("selectedTests",gson.toJsonTree(selected)); row.addProperty("selectedSha256",hash(selected)); caseRows.add(row);
      }
    }
    output.add("loader",loaderRows); output.add("cases",caseRows);
    Files.writeString(Path.of(args[1]),gson.toJson(output)+"\n",StandardCharsets.UTF_8);
  }
}

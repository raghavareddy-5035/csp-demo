import java.net.URI;
import java.net.http.*;

/** Java client. Run: javac StudyPulseClient.java && java StudyPulseClient URL API_KEY */
public class StudyPulseClient {
    public static void main(String[] args) throws Exception {
        String json = "{\"study_hours\":4,\"attendance\":85,\"sleep_hours\":7,\"previous_score\":70}";
        HttpRequest req = HttpRequest.newBuilder(URI.create(args[0] + "/api/predict"))
            .header("Content-Type", "application/json").header("X-API-Key", args[1])
            .POST(HttpRequest.BodyPublishers.ofString(json)).build();
        HttpResponse<String> res = HttpClient.newHttpClient().send(req, HttpResponse.BodyHandlers.ofString());
        System.out.println("HTTP " + res.statusCode() + " -> " + res.body());
    }
}

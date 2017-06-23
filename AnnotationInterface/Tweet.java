import java.util.ArrayList;

public class Tweet {

	private String tweetId;
	private String userId;
	private String text;
	private ArrayList<Token> tokens;
	
	
	public Tweet(String tweetId, String userId, String text) {
		super();
		this.tweetId = tweetId;
		this.userId = userId;
		this.text = text;
		this.tokens = new ArrayList<Token>();
	}
	
	public String getTweetId() {
		return tweetId;
	}
	public String getUserId() {
		return userId;
	}
	public String getText() {
		return text;
	}
	public ArrayList<Token> getTokens() {
		return tokens;
	}
	public void addToken(Token token){
		this.tokens.add(token);
	}
	public int getTokensLength(){
		return this.tokens.size();
	}
	public void setTokens(ArrayList<Token> tokens){
		this.tokens = tokens;
	}
}

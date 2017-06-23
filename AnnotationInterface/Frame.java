import java.awt.EventQueue;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.swing.DefaultCellEditor;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.ScrollPaneConstants;
import javax.swing.UIManager;
import javax.swing.table.DefaultTableModel;
import javax.swing.table.TableColumn;

import com.opencsv.CSVReader;
import com.opencsv.CSVWriter;

public class Frame {

	private static JFrame frame;
	public static ArrayList<Tweet> tweets = new ArrayList<Tweet>();
	private static JTextArea tweetText;
	private static JScrollPane scrollPane;
	private static JTable tbl;
	private static JButton btnNext;

	private static int CURRENT=0;
	private static JButton btnDelete;
	private static JButton btnPrevious;
	private static JLabel lbl_preview_title;
	private static JTextField txtGoto;
	private static JButton btnGo;
	private static String FILE="";
	private static int CLOSE = 0;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				if(args.length==0){
					System.out.println("Erabilera: java -jar Etiketatzailea.jar korpus-fitxategia");
					return;
				}
				FILE = args[0];
				Frame window = new Frame();
				window.frame.setVisible(true);
				if(CLOSE == 1){
					frame.setVisible(false);
					frame.dispose();
				}
			}
		});
	}

	/**
	 * Create the application.
	 */
	public Frame() {
		try{
			initialize();
			
			//==========================================================================
			//======================== READ CSV FILE ===================================
			CSVReader reader;
			try{
				reader = new CSVReader(new FileReader(FILE));
			}catch(FileNotFoundException fnfe){
				System.out.println("Ezin izan da fitxategia irakurri!");
				CLOSE = 1;
				return;
			}
			String [] line;
			reader.readNext(); //Skip first line
			while ((line = reader.readNext()) != null) {
				Tweet tweet = new Tweet(line[0], line[1], line[2]);
				if(line.length > 3){ //The tweet has already been tagged
					for(int i=4; i < (Integer.parseInt(line[3])*2)+4; i=i+2){
						tweet.addToken(new Token(line[i], line[i+1]));
					}
				}else{ //The tweet has not been tagged
					//These tokens should be automatically tagged
					Pattern p_user = Pattern.compile("@\\w+", Pattern.UNICODE_CHARACTER_CLASS | Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
					Pattern p_url = Pattern.compile("https?\\S*", Pattern.UNICODE_CHARACTER_CLASS | Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
					Pattern p_number = Pattern.compile("\\d+([.,]\\d+)?", Pattern.UNICODE_CHARACTER_CLASS | Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
					Pattern p_punct = Pattern.compile("[?¿.,;:!¡()/'\\-\"]+", Pattern.UNICODE_CHARACTER_CLASS | Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
					Pattern p_word = Pattern.compile("\\w+", Pattern.UNICODE_CHARACTER_CLASS | Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
					Pattern p_repetition = Pattern.compile("(\\w)\\1{3,}", Pattern.UNICODE_CHARACTER_CLASS | Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
					
					Pattern pattern = Pattern.compile("(@\\w+|#\\w+|https?\\S*|\\d+([.,]\\d+)?|\\w+|[?¿.,;:!¡()/'\\-\"]+|\\S)", Pattern.UNICODE_CHARACTER_CLASS | Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
					Matcher tokens = pattern.matcher(tweet.getText()); //Get tokens
					
					while (tokens.find()) {
						String token = tokens.group();
						if(p_user.matcher(token).matches()){
							tweet.addToken(new Token(token, "ID"));
						}else if(p_url.matcher(token).matches()){
							tweet.addToken(new Token(token, "URL"));
						}else if(p_number.matcher(token).matches()){
							tweet.addToken(new Token(token, "EG"));
						}else if(p_punct.matcher(token).matches()){
							tweet.addToken(new Token(token, "EG"));
						}else if(p_word.matcher(token).matches()){
							if(p_repetition.matcher(token).find()){
								String normalized = token.replaceAll("(\\w)\\1{3,}", "$1");
								tweet.addToken(new Token(normalized, "-"));
							}else{
								tweet.addToken(new Token(token, "-"));
							}
						}else{
							tweet.addToken(new Token(token, "-"));
						}
					}					
				}
				tweets.add(tweet);
				
			}
			reader.close();
			System.out.println("Tweets read: "+tweets.size());
			//==========================================================================

			showTweetInFrame(); //Show first tweet table

			//=============== NEXT BUTTON ACTION =======================================
			btnNext.addActionListener(new ActionListener(){ 
				public void actionPerformed(ActionEvent e){
					ArrayList<Token> temp = new ArrayList<Token>();
					for(int i=0; i < tbl.getModel().getRowCount(); i++){
						temp.add(new Token((String)tbl.getModel().getValueAt(i, 0), (String)tbl.getModel().getValueAt(i, 1)));
					}
					tweets.get(CURRENT).setTokens(temp);
					
					//SAVE
					saveTweets();					
					
					CURRENT++;
					if(CURRENT+1==tweets.size()){
						btnNext.setEnabled(false);
					}
					btnPrevious.setEnabled(true);
					showTweetInFrame();
				}
			});
			
			//=============== PREVIOUS BUTTON ACTION ====================================
			btnPrevious.addActionListener(new ActionListener(){
				public void actionPerformed(ActionEvent e){
					ArrayList<Token> temp = new ArrayList<Token>();
					for(int i=0; i < tbl.getModel().getRowCount(); i++){
						temp.add(new Token((String)tbl.getModel().getValueAt(i, 0), (String)tbl.getModel().getValueAt(i, 1)));
					}
					tweets.get(CURRENT).setTokens(temp);
					
					//SAVE
					saveTweets();
					
					CURRENT--;
					if(CURRENT==0){
						btnPrevious.setEnabled(false);
					}
					btnNext.setEnabled(true);
					showTweetInFrame();
				}
			});
			
			//=============== DELETE BUTTON ACTION ========================================
			btnDelete.addActionListener(new ActionListener(){
				public void actionPerformed(ActionEvent e){
					int dialogResult = JOptionPane.showConfirmDialog(frame, "Txioa ezabatu?", "Kontuz!", JOptionPane.YES_NO_CANCEL_OPTION, JOptionPane.QUESTION_MESSAGE);
					if(dialogResult == JOptionPane.YES_OPTION){
						CSVWriter writer;
						try {
							Tweet tweet = tweets.get(CURRENT);
							writer = new CSVWriter(new FileWriter("DeletedTweets.csv", true));
							ArrayList<String> list = new ArrayList<String>();
							list.add(tweet.getTweetId());
							list.add(tweet.getUserId());
							list.add(tweet.getText());
							String[] array = (String[]) list.toArray(new String[list.size()]);
							writer.writeNext(array);
							writer.close();
							tweets.remove(CURRENT);
							//SAVE
							saveTweets();
							
							showTweetInFrame();
						} catch (IOException e1) {
							e1.printStackTrace();
						}
					}
				}
			});
			
			
			//=============== GO BUTTON ACTION ===========================================
			btnGo.addActionListener(new ActionListener(){
				public void actionPerformed(ActionEvent e){
					int ind = 0;
					try{
						ind = Integer.valueOf(txtGoto.getText());
						txtGoto.setText("");
					}catch(NumberFormatException e3){
						JOptionPane.showMessageDialog(frame, "Kontuz!");
						txtGoto.setText("");
						return;
					}
					ArrayList<Token> temp = new ArrayList<Token>();
					for(int i=0; i < tbl.getModel().getRowCount(); i++){
						temp.add(new Token((String)tbl.getModel().getValueAt(i, 0), (String)tbl.getModel().getValueAt(i, 1)));
					}
					tweets.get(CURRENT).setTokens(temp);
					//SAVE
					saveTweets();
					
					if(ind-1>=0 && ind-1<tweets.size()){
						CURRENT = ind-1;
						btnNext.setEnabled(true);
						btnPrevious.setEnabled(true);
						if(CURRENT==0){
							btnPrevious.setEnabled(false);
						}else if(CURRENT+1==tweets.size()){
							btnNext.setEnabled(false);
						}
						showTweetInFrame();
					}else{
						JOptionPane.showMessageDialog(frame, "Kontuz!");
					}
				}
			});
			
		}catch(Exception e){
			e.getMessage();
		}
	}
	
	public void saveTweets(){
		CSVWriter writer;
		try {
			writer = new CSVWriter(new FileWriter("CodeSwitchingTweets.csv"), ',');
			String[] head = {"tweetId","userId","text","tags [token,tag]"};
			writer.writeNext(head);
			for(Tweet tweet : tweets){
				ArrayList<String> list = new ArrayList<String>();
				list.add(tweet.getTweetId());
				list.add(tweet.getUserId());
				list.add(tweet.getText());
				list.add(String.valueOf(tweet.getTokensLength()));
				for(Token token : tweet.getTokens()){
					list.add(token.getToken());
					list.add(token.getTag());
				}
				String[] array = (String[]) list.toArray(new String[list.size()]);
				writer.writeNext(array);
			}
			writer.close();
		} catch (IOException e1) {
			e1.printStackTrace();
		}
	}

	private void showTweetInFrame(){
		DefaultTableModel dtm = new DefaultTableModel(0, 0);
		String header[] = new String[] { "Tokena", "Etiketa" };
		dtm.setColumnIdentifiers(header);
		tbl.setModel(dtm);

		Tweet tweet = tweets.get(CURRENT);
		lbl_preview_title.setText("Txioa "+(CURRENT+1)+"/"+tweets.size());
		tweetText.setText(tweet.getText());


		String[] options = { "ES", "EUS", "ID", "URL", "IE", "NH", "ANB", "EG" };
		JComboBox sel_opts = new JComboBox(options);
		sel_opts.setSelectedIndex(1);
		TableColumn sportColumn = tbl.getColumnModel().getColumn(1);
		sportColumn.setCellEditor(new DefaultCellEditor(sel_opts));

		for(Token t : tweet.getTokens()){
			((DefaultTableModel)tbl.getModel()).addRow(new Object[] { t.getToken(), t.getTag() });
		}
	}

	/**
	 * Initialize the contents of the frame.
	 */
	private void initialize() {
		frame = new JFrame();
		frame.setResizable(false);
		frame.setBounds(50, 50, 850, 594);
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.setTitle("Etiketatzailea");
		frame.getContentPane().setLayout(null);

		JPanel previewPanel = new JPanel();
		previewPanel.setBounds(12, 12, 826, 80);

		lbl_preview_title = new JLabel("Txioa");
		lbl_preview_title.setBounds(12, 12, 70, 15);
		previewPanel.add(lbl_preview_title);

		tweetText = new JTextArea();
		tweetText.setWrapStyleWord(true);
		tweetText.setBackground(UIManager.getColor("Panel.background"));
		tweetText.setLineWrap(true);
		tweetText.setEditable(false);
		tweetText.setBounds(12, 39, 802, 29);	
		previewPanel.add(tweetText);

		frame.getContentPane().add(previewPanel);

		tbl = new JTable();
		DefaultTableModel dtm = new DefaultTableModel(0, 0);
		String header[] = new String[] { "Tokena", "Etiketa" };
		dtm.setColumnIdentifiers(header);
		tbl.setModel(dtm);
		tbl.setRowHeight(30);

		scrollPane = new JScrollPane(tbl);
		scrollPane.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
		scrollPane.setBounds(12, 104, 826, 408);
		tbl.setFillsViewportHeight(true);

		frame.getContentPane().add(scrollPane);

		btnNext = new JButton("Hurrengora");
		btnNext.setBounds(592, 529, 117, 25);
		frame.getContentPane().add(btnNext);

		btnDelete = new JButton("Ezabatu");
		btnDelete.setBounds(721, 529, 117, 25);
		frame.getContentPane().add(btnDelete);

		btnPrevious = new JButton("Aurrekora");
		btnPrevious.setBounds(463, 529, 117, 25);
		frame.getContentPane().add(btnPrevious);
		
		btnGo = new JButton("Joan");
		btnGo.setBounds(166, 529, 100, 25);
		frame.getContentPane().add(btnGo);
		
		txtGoto = new JTextField();
		txtGoto.setBounds(49, 529, 50, 25);
		frame.getContentPane().add(txtGoto);
		txtGoto.setColumns(10);
		
		JLabel lblJoan = new JLabel("Joan");
		lblJoan.setBounds(12, 534, 40, 15);
		frame.getContentPane().add(lblJoan);
		
		JLabel lblTxiora = new JLabel("txiora");
		lblTxiora.setBounds(104, 534, 70, 15);
		frame.getContentPane().add(lblTxiora);
	}
}

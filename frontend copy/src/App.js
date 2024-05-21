import logo from './logo.svg';
import './App.css';
import ChatBox from './components/ChatBox'

function App() {  

  return (
    <div className="App">
      <header className="App-header">
        <ChatBox />
      </header>
      <footer>
        <p>GPT Researcher &copy; 2023 | <a target="_blank" href="https://github.com/assafelovic/gpt-researcher">Github
                Page</a></p>
    </footer>
    </div>
  );
}

export default App;

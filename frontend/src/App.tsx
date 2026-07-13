import { Provider } from 'react-redux';
import { store } from './store';
import InteractionLog from './components/InteractionLog';

function App() {
  return (
    <Provider store={store}>
      <div className="min-h-screen bg-gray-100 p-4 font-sans">
        <header className="mb-4">
          <h1 className="text-2xl font-semibold text-gray-800">Log HCP Interaction</h1>
        </header>
        <InteractionLog />
      </div>
    </Provider>
  );
}

export default App;

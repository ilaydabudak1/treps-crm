import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the CRM login screen', () => {
  render(<App />);
  const linkElement = screen.getByText(/Treps CRM/i);
  expect(linkElement).toBeInTheDocument();
});

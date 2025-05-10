import { DynamicPricingPage } from '../features/pricing/DynamicPricingPage';

// ...existing imports...

export const Routes = () => {
  return (
    <Router>
      // ...existing routes...
      <Route path="/dynamic-pricing" element={<DynamicPricingPage />} />
      // ...existing routes...
    </Router>
  );
};
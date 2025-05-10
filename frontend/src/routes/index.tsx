import { CustomerList } from '../pages/customers/CustomerList';
import { CustomerAdd } from '../pages/customers/CustomerAdd';
import { CustomerEdit } from '../pages/customers/CustomerEdit';
import { pricingRoutes } from '../features/pricing/routes';
import installationRoutes from './installations';

export const routes = [
    {
        path: '/customers',
        element: <CustomerList />,
    },
    {
        path: '/customers/add',
        element: <CustomerAdd />,
    },
    {
        path: '/customers/edit/:id',
        element: <CustomerEdit />,
    },
    ...pricingRoutes,
    ...installationRoutes,
];

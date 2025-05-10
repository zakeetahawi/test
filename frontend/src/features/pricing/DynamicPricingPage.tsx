import React, { useState } from 'react';
import { Container, Box, Dialog, DialogContent, Tabs, Tab } from '@mui/material';
import { DynamicPricingList } from './DynamicPricingList';
import { DynamicPricingForm } from './DynamicPricingForm';
import { DynamicPricingDetails } from './DynamicPricingDetails';
import { PricingAnalytics } from './PricingAnalytics';
import { PricingRuleTest } from './PricingRuleTest';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`pricing-tabpanel-${index}`}
      aria-labelledby={`pricing-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const DynamicPricingPage: React.FC = () => {
  const [selectedRuleId, setSelectedRuleId] = useState<number | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleRuleSelect = (ruleId: number) => {
    setSelectedRuleId(ruleId);
  };

  const handleAddNew = () => {
    setEditingRule(null);
    setIsFormOpen(true);
  };

  const handleEdit = (rule: any) => {
    setEditingRule(rule);
    setIsFormOpen(true);
  };

  const handleFormClose = () => {
    setIsFormOpen(false);
    setEditingRule(null);
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="pricing management tabs">
          <Tab label="قواعد التسعير" />
          <Tab label="التحليلات" />
          <Tab label="اختبار القواعد" />
        </Tabs>
      </Box>

      <TabPanel value={activeTab} index={0}>
        <Box display="flex" gap={4}>
          {/* قائمة القواعد */}
          <Box flex={1}>
            <DynamicPricingList
              onRuleSelect={handleRuleSelect}
              onAddNew={handleAddNew}
              onEdit={handleEdit}
            />
          </Box>

          {/* تفاصيل القاعدة المحددة */}
          {selectedRuleId && (
            <Box flex={1}>
              <DynamicPricingDetails ruleId={selectedRuleId} />
            </Box>
          )}
        </Box>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <PricingAnalytics />
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <PricingRuleTest />
      </TabPanel>

      {/* نموذج إضافة/تعديل قاعدة */}
      <Dialog
        open={isFormOpen}
        onClose={handleFormClose}
        maxWidth="md"
        fullWidth
      >
        <DialogContent>
          <DynamicPricingForm
            initialData={editingRule}
            onSuccess={handleFormClose}
          />
        </DialogContent>
      </Dialog>
    </Container>
  );
};
'use client';

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Save, TestTube, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { useAdapters } from '@/hooks/useAdapters';
import { AdapterConfiguration, ProviderType } from '@/types/adapters';

// Form validation schema
const adapterConfigSchema = z.object({
  provider_name: z.enum(['alpha_vantage', 'yahoo_finance', 'iex_cloud', 'polygon', 'finnhub']),
  display_name: z.string().min(1, 'Display name is required').max(100, 'Display name too long'),
  description: z.string().max(500, 'Description too long').optional(),
  is_active: z.boolean().default(false),
  api_key: z.string().optional(),
  base_url: z.string().url('Invalid URL format').optional(),
  timeout: z.number().min(1).max(300).optional(),
  rate_limit_per_minute: z.number().min(1).max(1000).optional(),
  rate_limit_per_day: z.number().min(1).max(100000).optional(),
  cost_per_call: z.number().min(0).optional(),
  daily_budget: z.number().min(0).optional(),
  monthly_budget: z.number().min(0).optional(),
  priority: z.number().min(1).max(100).default(10),
});

type FormData = z.infer<typeof adapterConfigSchema>;

interface AdapterConfigFormProps {
  adapter?: AdapterConfiguration;
  onSave?: (adapter: AdapterConfiguration) => void;
  onCancel?: () => void;
  onTest?: (config: FormData) => Promise<boolean>;
}

const PROVIDER_CONFIGS = {
  alpha_vantage: {
    name: 'Alpha Vantage',
    description: 'Professional-grade financial data APIs',
    requiredFields: ['api_key'],
    optionalFields: ['base_url', 'timeout', 'rate_limit_per_minute'],
    defaultUrl: 'https://www.alphavantage.co/query',
    costPerCall: 0.02,
    rateLimit: 100,
  },
  yahoo_finance: {
    name: 'Yahoo Finance',
    description: 'Free financial data with rate limitations',
    requiredFields: [],
    optionalFields: ['base_url', 'timeout', 'rate_limit_per_minute'],
    defaultUrl: 'https://query1.finance.yahoo.com',
    costPerCall: 0.0,
    rateLimit: 200,
  },
  iex_cloud: {
    name: 'IEX Cloud',
    description: 'Reliable market data with flexible pricing',
    requiredFields: ['api_key'],
    optionalFields: ['base_url', 'timeout', 'rate_limit_per_minute'],
    defaultUrl: 'https://cloud.iexapis.com',
    costPerCall: 0.01,
    rateLimit: 500,
  },
  polygon: {
    name: 'Polygon',
    description: 'Real-time and historical market data',
    requiredFields: ['api_key'],
    optionalFields: ['base_url', 'timeout', 'rate_limit_per_minute'],
    defaultUrl: 'https://api.polygon.io',
    costPerCall: 0.005,
    rateLimit: 1000,
  },
  finnhub: {
    name: 'Finnhub',
    description: 'Real-time financial data APIs',
    requiredFields: ['api_key'],
    optionalFields: ['base_url', 'timeout', 'rate_limit_per_minute'],
    defaultUrl: 'https://finnhub.io/api/v1',
    costPerCall: 0.02,
    rateLimit: 60,
  },
};

const AdapterConfigForm: React.FC<AdapterConfigFormProps> = ({
  adapter,
  onSave,
  onCancel,
  onTest,
}) => {
  const [showApiKey, setShowApiKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const { createAdapter, updateAdapter, validateConfig } = useAdapters();

  const form = useForm<FormData>({
    resolver: zodResolver(adapterConfigSchema),
    defaultValues: {
      provider_name: adapter?.provider_name || 'alpha_vantage',
      display_name: adapter?.display_name || '',
      description: adapter?.config_data?.description || '',
      is_active: adapter?.is_active || false,
      api_key: adapter?.config_data?.api_key || '',
      base_url: adapter?.config_data?.base_url || '',
      timeout: adapter?.config_data?.timeout || 30,
      rate_limit_per_minute: adapter?.config_data?.rate_limit_per_minute || 100,
      rate_limit_per_day: adapter?.config_data?.rate_limit_per_day || 5000,
      cost_per_call: adapter?.config_data?.cost_per_call || 0,
      daily_budget: adapter?.config_data?.daily_budget || 10,
      monthly_budget: adapter?.config_data?.monthly_budget || 250,
      priority: adapter?.config_data?.priority || 10,
    },
  });

  const selectedProvider = form.watch('provider_name');
  const providerConfig = PROVIDER_CONFIGS[selectedProvider];

  // Update form defaults when provider changes
  useEffect(() => {
    if (providerConfig && !adapter) {
      form.setValue('base_url', providerConfig.defaultUrl);
      form.setValue('rate_limit_per_minute', providerConfig.rateLimit);
      form.setValue('cost_per_call', providerConfig.costPerCall);
    }
  }, [selectedProvider, providerConfig, form, adapter]);

  const handleTest = async () => {
    const formData = form.getValues();

    try {
      setTesting(true);
      setTestResult(null);

      // Validate configuration
      const isValid = await validateConfig(formData.provider_name, {
        api_key: formData.api_key,
        base_url: formData.base_url,
        timeout: formData.timeout,
      });

      if (onTest) {
        const testSuccess = await onTest(formData);
        setTestResult({
          success: testSuccess,
          message: testSuccess
            ? 'Configuration test successful!'
            : 'Configuration test failed. Please check your settings.'
        });
      } else {
        setTestResult({
          success: isValid,
          message: isValid
            ? 'Configuration is valid!'
            : 'Configuration validation failed.'
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: `Test failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    } finally {
      setTesting(false);
    }
  };

  const onSubmit = async (data: FormData) => {
    try {
      const configData = {
        api_key: data.api_key,
        base_url: data.base_url,
        timeout: data.timeout,
        rate_limit_per_minute: data.rate_limit_per_minute,
        rate_limit_per_day: data.rate_limit_per_day,
        cost_per_call: data.cost_per_call,
        daily_budget: data.daily_budget,
        monthly_budget: data.monthly_budget,
        priority: data.priority,
        description: data.description,
      };

      const adapterData = {
        provider_name: data.provider_name,
        display_name: data.display_name,
        config_data: configData,
        is_active: data.is_active,
      };

      if (adapter) {
        // Update existing adapter
        const updatedAdapter = await updateAdapter(adapter.id, adapterData);
        if (onSave) {
          onSave(updatedAdapter);
        }
      } else {
        // Create new adapter
        const newAdapter = await createAdapter(adapterData);
        if (onSave) {
          onSave(newAdapter);
        }
      }
    } catch (error) {
      console.error('Failed to save adapter:', error);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {adapter ? 'Edit Adapter Configuration' : 'Create New Adapter'}
        </CardTitle>
        <CardDescription>
          Configure market data provider settings and credentials
        </CardDescription>
      </CardHeader>

      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="basic">Basic</TabsTrigger>
                <TabsTrigger value="connection">Connection</TabsTrigger>
                <TabsTrigger value="limits">Limits</TabsTrigger>
                <TabsTrigger value="cost">Cost</TabsTrigger>
              </TabsList>

              {/* Basic Configuration */}
              <TabsContent value="basic" className="space-y-4">
                <FormField
                  control={form.control}
                  name="provider_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Provider Type</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select a provider" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {Object.entries(PROVIDER_CONFIGS).map(([key, config]) => (
                            <SelectItem key={key} value={key}>
                              {config.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>{providerConfig?.description}</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="display_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Display Name</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g., Primary Alpha Vantage" {...field} />
                      </FormControl>
                      <FormDescription>
                        A human-readable name for this adapter configuration
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description (Optional)</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Additional notes about this adapter..."
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="is_active"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                      <div className="space-y-0.5">
                        <FormLabel className="text-base">Active</FormLabel>
                        <FormDescription>
                          Enable this adapter for use in market data requests
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </TabsContent>

              {/* Connection Settings */}
              <TabsContent value="connection" className="space-y-4">
                {providerConfig?.requiredFields.includes('api_key') && (
                  <FormField
                    control={form.control}
                    name="api_key"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>API Key</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Input
                              type={showApiKey ? 'text' : 'password'}
                              placeholder="Enter your API key"
                              {...field}
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="absolute right-0 top-0 h-full px-3"
                              onClick={() => setShowApiKey(!showApiKey)}
                            >
                              {showApiKey ? (
                                <EyeOff className="h-4 w-4" />
                              ) : (
                                <Eye className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </FormControl>
                        <FormDescription>
                          Your {providerConfig?.name} API key
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                )}

                <FormField
                  control={form.control}
                  name="base_url"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Base URL</FormLabel>
                      <FormControl>
                        <Input placeholder="https://api.example.com" {...field} />
                      </FormControl>
                      <FormDescription>
                        API endpoint base URL (leave default unless custom endpoint needed)
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="timeout"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Timeout (seconds)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min="1"
                          max="300"
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription>
                        Request timeout in seconds (1-300)
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>

              {/* Rate Limits */}
              <TabsContent value="limits" className="space-y-4">
                <FormField
                  control={form.control}
                  name="rate_limit_per_minute"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Rate Limit (per minute)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min="1"
                          max="1000"
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription>
                        Maximum requests per minute (recommended: {providerConfig?.rateLimit})
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="rate_limit_per_day"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Rate Limit (per day)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min="1"
                          max="100000"
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription>
                        Maximum requests per day
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="priority"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Priority</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min="1"
                          max="100"
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription>
                        Priority for fallback ordering (1 = highest priority)
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>

              {/* Cost Management */}
              <TabsContent value="cost" className="space-y-4">
                <FormField
                  control={form.control}
                  name="cost_per_call"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Cost per Call (USD)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.001"
                          min="0"
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription>
                        Cost per API call in USD (typical: ${providerConfig?.costPerCall})
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="daily_budget"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Daily Budget (USD)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription>
                        Daily spending limit in USD
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="monthly_budget"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Monthly Budget (USD)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription>
                        Monthly spending limit in USD
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>
            </Tabs>

            {/* Test Result */}
            {testResult && (
              <Alert variant={testResult.success ? 'default' : 'destructive'}>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{testResult.message}</AlertDescription>
              </Alert>
            )}

            {/* Form Actions */}
            <div className="flex items-center justify-between pt-6 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={handleTest}
                disabled={testing}
              >
                <TestTube className="w-4 h-4 mr-2" />
                {testing ? 'Testing...' : 'Test Configuration'}
              </Button>

              <div className="flex items-center gap-2">
                {onCancel && (
                  <Button type="button" variant="outline" onClick={onCancel}>
                    Cancel
                  </Button>
                )}
                <Button type="submit">
                  <Save className="w-4 h-4 mr-2" />
                  {adapter ? 'Update Adapter' : 'Create Adapter'}
                </Button>
              </div>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
};

export default AdapterConfigForm;
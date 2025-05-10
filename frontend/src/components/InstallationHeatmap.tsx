import React from 'react';
import { Box, Paper, Typography, useTheme } from '@mui/material';
import { ResponsiveHeatMap } from '@nivo/heatmap';

interface HeatmapDataPoint {
  region: string;
  hour: string;
  value: number;
}

interface Props {
  data: HeatmapDataPoint[];
}

export const InstallationHeatmap: React.FC<Props> = ({ data }) => {
  const theme = useTheme();

  // Transform data for Nivo heatmap
  const transformedData = React.useMemo(() => {
    const regions = Array.from(new Set(data.map(d => d.region)));
    const hours = Array.from(new Set(data.map(d => d.hour)));

    return hours.map(hour => ({
      id: hour,
      data: regions.map(region => {
        const point = data.find(d => d.hour === hour && d.region === region);
        return {
          x: region,
          y: point?.value ?? 0
        };
      })
    }));
  }, [data]);

  return (
    <Paper sx={{ p: 2, height: 400 }}>
      <Typography variant="h6" gutterBottom align="center">
        توزيع التركيبات حسب المنطقة والوقت
      </Typography>
      <Box sx={{ height: 350 }}>
        <ResponsiveHeatMap
          data={transformedData}
          margin={{ top: 20, right: 90, bottom: 60, left: 90 }}
          valueFormat=">-.2s"
          axisTop={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: -45,
            legend: 'المنطقة',
            legendPosition: 'middle',
            legendOffset: -40
          }}
          axisLeft={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: 0,
            legend: 'الساعة',
            legendPosition: 'middle',
            legendOffset: -60
          }}
          colors={{
            type: 'sequential',
            scheme: 'blues'
          }}
          emptyColor="#eeeeee"
          borderWidth={1}
          borderColor={theme.palette.divider}
          enableLabels={true}
          labelTextColor={{
            from: 'color',
            modifiers: [['darker', 2]]
          }}
          animate={true}
          motionConfig="gentle"
          theme={{
            axis: {
              ticks: {
                text: {
                  fill: theme.palette.text.primary,
                  fontSize: 12,
                },
              },
              legend: {
                text: {
                  fill: theme.palette.text.primary,
                  fontSize: 14,
                },
              },
            },
            legends: {
              text: {
                fill: theme.palette.text.primary,
                fontSize: 12,
              },
            },
            tooltip: {
              container: {
                background: theme.palette.background.paper,
                color: theme.palette.text.primary,
                fontSize: 12,
                borderRadius: 4,
                boxShadow: theme.shadows[2],
              },
            },
          }}
          legends={[
            {
              anchor: 'bottom',
              translateY: 40,
              translateX: 0,
              length: 100,
              thickness: 8,
              direction: 'row',
              tickPosition: 'after',
              tickSize: 3,
              tickSpacing: 4,
              tickOverlap: false,
              title: 'عدد التركيبات',
              titleAlign: 'start',
              titleOffset: 4
            }
          ]}
        />
      </Box>
    </Paper>
  );
};
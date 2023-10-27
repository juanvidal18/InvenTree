import { Group, Paper, Space, Stack, Text } from '@mantine/core';
import { ReactNode } from 'react';

import { ApiImage } from '../images/ApiImage';
import { StylishText } from '../items/StylishText';
import { Breadcrumb, BreadcrumbList } from './BreadcrumbList';

/**
 * Construct a "standard" page detail for common display between pages.
 *
 * @param breadcrumbs - The breadcrumbs to display (optional)
 * @param
 */
export function PageDetail({
  title,
  subtitle,
  detail,
  imageUrl,
  breadcrumbs,
  actions
}: {
  title?: string;
  subtitle?: string;
  imageUrl?: string;
  detail?: ReactNode;
  breadcrumbs?: Breadcrumb[];
  actions?: ReactNode[];
}) {
  return (
    <Stack spacing="xs">
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Paper p="xs" radius="xs" shadow="xs">
          <BreadcrumbList breadcrumbs={breadcrumbs} />
        </Paper>
      )}
      <Paper p="xs" radius="xs" shadow="xs">
        <Stack spacing="xs">
          <Group position="apart" noWrap={true}>
            <Group position="left" noWrap={true}>
              {imageUrl && (
                <ApiImage src={imageUrl} radius="sm" height={64} width={64} />
              )}
              <Stack spacing="xs">
                {title && <StylishText size="lg">{title}</StylishText>}
                {subtitle && (
                  <Text size="md" truncate>
                    {subtitle}
                  </Text>
                )}
              </Stack>
            </Group>
            <Space />
            {detail}
            <Space />
            {actions && (
              <Group spacing={5} position="right">
                {actions}
              </Group>
            )}
          </Group>
        </Stack>
      </Paper>
    </Stack>
  );
}

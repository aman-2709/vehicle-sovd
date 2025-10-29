/**
 * Layout Component Tests
 *
 * Tests for main application layout wrapper.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from '../../src/components/common/Layout';
import * as AuthContext from '../../src/context/AuthContext';

// Mock Header and Sidebar components
vi.mock('../../src/components/common/Header', () => ({
  default: () => <div data-testid="header">Header</div>,
}));

vi.mock('../../src/components/common/Sidebar', () => ({
  default: () => <div data-testid="sidebar">Sidebar</div>,
}));

describe('Layout Component', () => {
  beforeEach(() => {
    // Mock useAuth hook
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        user_id: '1',
        username: 'testuser',
        role: 'engineer',
      },
      login: vi.fn(),
      logout: vi.fn(),
      refreshToken: vi.fn(),
    });
  });

  describe('Rendering', () => {
    it('renders header component', () => {
      render(
        <MemoryRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );

      expect(screen.getByTestId('header')).toBeInTheDocument();
    });

    it('renders sidebar component', () => {
      render(
        <MemoryRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );

      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    });

    it('renders children content', () => {
      render(
        <MemoryRouter>
          <Layout>
            <div>Page Content</div>
          </Layout>
        </MemoryRouter>
      );

      expect(screen.getByText('Page Content')).toBeInTheDocument();
    });

    it('renders all three sections together', () => {
      render(
        <MemoryRouter>
          <Layout>
            <div>Main Content</div>
          </Layout>
        </MemoryRouter>
      );

      expect(screen.getByTestId('header')).toBeInTheDocument();
      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByText('Main Content')).toBeInTheDocument();
    });
  });

  describe('Children Rendering', () => {
    it('renders simple text children', () => {
      render(
        <MemoryRouter>
          <Layout>Simple Text</Layout>
        </MemoryRouter>
      );

      expect(screen.getByText('Simple Text')).toBeInTheDocument();
    });

    it('renders complex component children', () => {
      const ComplexChild = () => (
        <div>
          <h1>Page Title</h1>
          <p>Page description</p>
          <button>Action Button</button>
        </div>
      );

      render(
        <MemoryRouter>
          <Layout>
            <ComplexChild />
          </Layout>
        </MemoryRouter>
      );

      expect(screen.getByText('Page Title')).toBeInTheDocument();
      expect(screen.getByText('Page description')).toBeInTheDocument();
      expect(screen.getByText('Action Button')).toBeInTheDocument();
    });

    it('renders multiple child elements', () => {
      render(
        <MemoryRouter>
          <Layout>
            <div>First Section</div>
            <div>Second Section</div>
            <div>Third Section</div>
          </Layout>
        </MemoryRouter>
      );

      expect(screen.getByText('First Section')).toBeInTheDocument();
      expect(screen.getByText('Second Section')).toBeInTheDocument();
      expect(screen.getByText('Third Section')).toBeInTheDocument();
    });

    it('renders nested component hierarchy', () => {
      render(
        <MemoryRouter>
          <Layout>
            <div>
              <div>
                <div>Deeply Nested Content</div>
              </div>
            </div>
          </Layout>
        </MemoryRouter>
      );

      expect(screen.getByText('Deeply Nested Content')).toBeInTheDocument();
    });
  });

  describe('Structure', () => {
    it('applies correct main component structure', () => {
      const { container } = render(
        <MemoryRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );

      const mainElement = container.querySelector('main');
      expect(mainElement).toBeInTheDocument();
    });

    it('includes toolbar spacer', () => {
      const { container } = render(
        <MemoryRouter>
          <Layout>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );

      const toolbars = container.querySelectorAll('.MuiToolbar-root');
      expect(toolbars.length).toBeGreaterThan(0);
    });
  });
});

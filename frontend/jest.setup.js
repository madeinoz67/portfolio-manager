import '@testing-library/jest-dom'

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}

  observe() {
    return null
  }

  disconnect() {
    return null
  }

  unobserve() {
    return null
  }
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor(cb) {
    this.cb = cb
  }

  observe() {
    return null
  }

  disconnect() {
    return null
  }

  unobserve() {
    return null
  }
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true,
})

// Mock fetch for all tests
global.fetch = jest.fn()

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
global.localStorage = localStorageMock

// Mock process.env
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8001'

// Reset all mocks after each test
afterEach(() => {
  jest.clearAllMocks()
})

// Mock AbortController
global.AbortController = class AbortController {
  signal = { aborted: false }
  abort = jest.fn(() => {
    this.signal.aborted = true
  })
}

// Mock setTimeout and clearTimeout for timeout testing
const originalSetTimeout = global.setTimeout
const originalClearTimeout = global.clearTimeout
global.setTimeout = jest.fn((cb, delay) => originalSetTimeout(cb, delay))
global.clearTimeout = jest.fn((id) => originalClearTimeout(id))

// Mock Next.js router
const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  prefetch: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
};

jest.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

// Export the router mock for tests to access
global.mockRouter = mockRouter;
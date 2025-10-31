namespace MyApp.Services
{
    using System;
    using System.Collections.Generic;
    using System.Linq;

    /// <summary>
    /// Service for managing user operations.
    /// </summary>
    public class UserService
    {
        private readonly IUserRepository _userRepository;
        private readonly IEmailService _emailService;

        /// <summary>
        /// Initializes a new instance of the UserService.
        /// </summary>
        public UserService(IUserRepository userRepository, IEmailService emailService)
        {
            _userRepository = userRepository ?? throw new ArgumentNullException(nameof(userRepository));
            _emailService = emailService ?? throw new ArgumentNullException(nameof(emailService));
        }

        /// <summary>
        /// Creates a new user account.
        /// </summary>
        /// <param name="email">User's email address</param>
        /// <param name="name">User's full name</param>
        /// <returns>The created user</returns>
        public async Task<User> CreateUserAsync(string email, string name)
        {
            // Validate email
            if (string.IsNullOrWhiteSpace(email))
                throw new ArgumentException("Email cannot be empty", nameof(email));

            // Check if user already exists
            var existingUser = await _userRepository.GetByEmailAsync(email);
            if (existingUser != null)
                throw new InvalidOperationException("User already exists");

            // Create new user
            var user = new User
            {
                Id = Guid.NewGuid(),
                Email = email,
                Name = name,
                CreatedAt = DateTime.UtcNow,
                IsActive = true
            };

            // Save to database
            await _userRepository.SaveAsync(user);

            // Send welcome email
            await _emailService.SendWelcomeEmailAsync(user);

            return user;
        }

        /// <summary>
        /// Authenticates a user with email and password.
        /// </summary>
        public async Task<AuthResult> AuthenticateAsync(string email, string password)
        {
            var user = await _userRepository.GetByEmailAsync(email);
            if (user == null || !user.VerifyPassword(password))
            {
                return AuthResult.Failed("Invalid credentials");
            }

            if (!user.IsActive)
            {
                return AuthResult.Failed("Account is inactive");
            }

            var token = GenerateJwtToken(user);
            return AuthResult.Success(token, user);
        }

        /// <summary>
        /// Retrieves all active users.
        /// </summary>
        public async Task<List<User>> GetActiveUsersAsync()
        {
            var allUsers = await _userRepository.GetAllAsync();
            return allUsers.Where(u => u.IsActive).ToList();
        }

        private string GenerateJwtToken(User user)
        {
            // JWT generation logic here
            return $"jwt_token_for_{user.Id}";
        }
    }
}

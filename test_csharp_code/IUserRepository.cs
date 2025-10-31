namespace MyApp.Services
{
    using System;
    using System.Collections.Generic;
    using System.Threading.Tasks;

    /// <summary>
    /// Repository interface for user data access.
    /// </summary>
    public interface IUserRepository
    {
        /// <summary>
        /// Gets a user by their unique identifier.
        /// </summary>
        Task<User> GetByIdAsync(Guid id);

        /// <summary>
        /// Gets a user by their email address.
        /// </summary>
        Task<User> GetByEmailAsync(string email);

        /// <summary>
        /// Retrieves all users from the database.
        /// </summary>
        Task<List<User>> GetAllAsync();

        /// <summary>
        /// Saves a user to the database.
        /// </summary>
        Task SaveAsync(User user);

        /// <summary>
        /// Deletes a user from the database.
        /// </summary>
        Task DeleteAsync(Guid id);
    }
}
